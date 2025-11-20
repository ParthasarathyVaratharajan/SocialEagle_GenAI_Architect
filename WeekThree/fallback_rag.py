import os
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WikipediaLoader
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

# Fallback Mechanism RAG sample
# - Try primary retrieval strategy; if it fails or returns low-quality results, fall back to alternatives
# - Try primary LLM; if it fails, fall back to a cheaper/faster model
# - Graceful degradation: maintain service quality even when some components fail

# Require OPENAI_API_KEY
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable not set. Set it before running the script.")

# 1) Load documents and split
print("Loading source document...")
loader = WikipediaLoader("Artificial intelligence", lang="en", load_max_docs=1)
docs = loader.load()
if not docs:
    raise SystemExit("No documents loaded. Check network or loader settings.")

text = docs[0].page_content
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = splitter.split_text(text)
print(f"Created {len(chunks)} chunks from source.\n")

# 2) Build embeddings + vector store (Chroma)
print("Building embeddings and Chroma vector store...")
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
db_path = "./chroma_fallback_rag_db"
try:
    from shutil import rmtree
    if os.path.exists(db_path):
        rmtree(db_path)
except Exception:
    pass

vectordb = Chroma.from_texts(chunks, embedding=embeddings, persist_directory=db_path, collection_name="fallback_rag")

# 3) Initialize primary and fallback LLMs
print("Loading LLM models...")
primary_llm = ChatOpenAI(model="gpt-4", temperature=0.0, api_key=api_key)
fallback_llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.0, api_key=api_key)

# 4) Retrieval strategies
def retrieve_with_strategy(query, strategy="similarity"):
    """Try retrieval with specified strategy."""
    try:
        if strategy == "similarity":
            retriever = vectordb.as_retriever(search_type="similarity", search_kwargs={"k": 4})
        elif strategy == "mmr":
            retriever = vectordb.as_retriever(search_type="mmr", search_kwargs={"k": 4, "fetch_k": 15})
        elif strategy == "threshold":
            retriever = vectordb.as_retriever(
                search_type="similarity_score_threshold",
                search_kwargs={"k": 10, "score_threshold": 0.5}
            )
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
        
        docs = retriever.invoke(query)
        if not docs:
            return None, f"Strategy '{strategy}' returned no results"
        return docs, None
    except Exception as e:
        return None, str(e)

# 5) Generate answer with fallback LLM
def generate_with_fallback(context, query):
    """Try generating answer with primary LLM; fall back to cheaper model on failure."""
    answer_prompt = ChatPromptTemplate.from_template(
        """Answer the question based on the provided context. Be concise and accurate.
Context: {context}
Question: {query}
Answer:"""
    )
    
    # Try primary LLM
    print("  Attempting with primary LLM (gpt-4)...")
    try:
        chain = answer_prompt | primary_llm
        result = chain.invoke({"context": context[:2000], "query": query})
        return result.content, "primary"
    except Exception as e:
        print(f"  Primary LLM failed: {e}")
        print("  Falling back to gpt-3.5-turbo...")
        try:
            chain = answer_prompt | fallback_llm
            result = chain.invoke({"context": context[:2000], "query": query})
            return result.content, "fallback"
        except Exception as e2:
            return None, str(e2)

# 6) Evaluate answer quality
def evaluate_answer_quality(answer):
    """Simple heuristic: check if answer has minimum length and content."""
    if not answer or len(answer.strip()) < 50:
        return False, "Answer too short or empty"
    if answer.lower() == "i don't know" or "cannot" in answer.lower():
        return False, "Answer indicates insufficient information"
    return True, "OK"

# Main pipeline
query = "What are the key applications of artificial intelligence in modern society?"
print(f"Query: {query}\n")
print("="*80 + "\n")

# STEP 1: Retrieval with fallback
print("STEP 1: Retrieval with Fallback Mechanism")
strategies = ["similarity", "mmr", "threshold"]
retrieved_docs = None
used_strategy = None

for strategy in strategies:
    print(f"  Trying {strategy} strategy...")
    docs, error = retrieve_with_strategy(query, strategy)
    if docs:
        retrieved_docs = docs
        used_strategy = strategy
        print(f"  Success with {strategy} strategy! Retrieved {len(docs)} documents.\n")
        break
    else:
        print(f"  Failed: {error}")

if not retrieved_docs:
    print("All retrieval strategies failed. Cannot proceed.\n")
else:
    context = "\n\n".join([d.page_content for d in retrieved_docs[:6]])
    print(f"Using context from '{used_strategy}' strategy.\n")
    
    # STEP 2: Generate answer with fallback LLM
    print("STEP 2: Generating Answer with Fallback LLM")
    answer, llm_used = generate_with_fallback(context, query)
    
    if answer:
        print(f"Answer generated using {llm_used} LLM.\n")
        
        # STEP 3: Evaluate answer quality
        print("STEP 3: Evaluating Answer Quality")
        is_good, feedback = evaluate_answer_quality(answer)
        print(f"  Quality check: {feedback}\n")
        
        if not is_good:
            print("  Low quality answer detected. Attempting regeneration with more context...")
            # Retrieve more context and try again
            more_context = context + "\n\n" + "\n\n".join([d.page_content for d in retrieved_docs[6:]])
            answer, _ = generate_with_fallback(more_context, query)
        
        print("--- Final Answer ---\n")
        print(answer)
    else:
        print(f"Failed to generate answer: {llm_used}\n")

print("\n" + "="*80)
print("Fallback RAG pipeline complete.")
