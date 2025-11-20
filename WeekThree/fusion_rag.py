import os
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WikipediaLoader
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

# Check for OpenAI API key
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable not set.")

# Load and split documents
print("Loading documents...")
loaders = [
    ("Python", WikipediaLoader("Python (programming language)", lang="en", load_max_docs=1)),
    ("Data Science", WikipediaLoader("Data Science", lang="en", load_max_docs=1))
]

all_chunks = []
for name, loader in loaders:
    docs = loader.load()
    if docs:
        text = docs[0].page_content
        splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=30)
        chunks = splitter.split_text(text)
        all_chunks.extend(chunks)
        print(f"  {name}: {len(chunks)} chunks")

print(f"Total chunks: {len(all_chunks)}\n")

# Initialize HuggingFace Embeddings
print("Loading embedding model...")
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# Create FAISS vector store
print("Building FAISS vector store...")
db = FAISS.from_texts(all_chunks, embedding=embeddings)
print("FAISS vector store created.\n")

# Initialize OpenAI LLM
print("Loading OpenAI ChatGPT...")
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7, api_key=api_key)

# Fusion RAG Pipeline
query = "How is Python used in data science?"
print(f"Query: {query}")
print("="*80 + "\n")

# Step 1: Multiple Retrieval Strategies
print("STEP 1: Fusion Retrieval - Multiple Strategies")

# Strategy 1: Similarity Search
print("  Strategy 1: Similarity Search (k=3)")
retriever_similarity = db.as_retriever(search_type="similarity", search_kwargs={"k": 3})
docs_similarity = retriever_similarity.invoke(query)
print(f"    Retrieved {len(docs_similarity)} documents\n")

# Strategy 2: MMR (Maximal Marginal Relevance)
print("  Strategy 2: MMR - Diversity-aware (k=3)")
retriever_mmr = db.as_retriever(search_type="mmr", search_kwargs={"k": 3, "fetch_k": 15})
docs_mmr = retriever_mmr.invoke(query)
print(f"    Retrieved {len(docs_mmr)} documents\n")

# Strategy 3: Similarity with Score Threshold
print("  Strategy 3: Similarity with Score Threshold (score >= 0.5)")
retriever_threshold = db.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={"k": 10, "score_threshold": 0.5}
)
docs_threshold = retriever_threshold.invoke(query)
print(f"    Retrieved {len(docs_threshold)} documents\n")

# Step 2: Merge and Deduplicate Results
print("STEP 2: Merging and Deduplicating Results")
all_retrieved = docs_similarity + docs_mmr + docs_threshold

# Deduplicate by content
seen = set()
merged_docs = []
for doc in all_retrieved:
    content_hash = hash(doc.page_content[:100])
    if content_hash not in seen:
        seen.add(content_hash)
        merged_docs.append(doc)

print(f"Total after merge: {len(all_retrieved)} documents")
print(f"After deduplication: {len(merged_docs)} unique documents\n")

context = "\n\n".join([doc.page_content for doc in merged_docs[:5]])

# Step 3: Generate Answer with Fused Context
print("STEP 3: Generating Answer with Fused Context")
rag_prompt = ChatPromptTemplate.from_template(
    """Answer the question based on the provided context from multiple retrieval strategies.
    Context: {context}
    Question: {query}
    Answer:"""
)

rag_chain = rag_prompt | llm
answer = rag_chain.invoke({"query": query, "context": context})
print(answer.content)
print()

# Step 4: Evaluate Answer Quality
print("STEP 4: Evaluating Answer Quality")
evaluation_prompt = ChatPromptTemplate.from_template(
    """Evaluate if this answer is comprehensive and well-grounded.
    Question: {query}
    Answer: {answer}
    
    Provide:
    - Coverage score (1-5): How much of the question is answered
    - Accuracy score (1-5): How accurate the information is
    - Overall assessment"""
)

eval_chain = evaluation_prompt | llm
evaluation = eval_chain.invoke({
    "query": query,
    "answer": answer.content
})
print(evaluation.content)
print()

print("="*80)
print("Fusion RAG pipeline complete!")
