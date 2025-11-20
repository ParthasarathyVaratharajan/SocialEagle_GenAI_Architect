import os
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WikipediaLoader
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

# Adaptive RAG sample
# - Classify query complexity (simple, moderate, complex)
# - Adapt chunk size: simple queries use larger chunks (less context); complex use smaller chunks (more detail)
# - Adapt retrieval strategy: simple queries use similarity; complex use MMR for diversity
# - Adapt num_results: simple need fewer results; complex need more
# - Dynamic adaptation optimizes cost, latency, and quality

# Require OPENAI_API_KEY
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable not set. Set it before running the script.")

# 1) Load documents
print("Loading source document...")
loader = WikipediaLoader("Artificial intelligence", lang="en", load_max_docs=1)
docs = loader.load()
if not docs:
    raise SystemExit("No documents loaded. Check network or loader settings.")

text = docs[0].page_content
print(f"Document loaded: {len(text)} characters\n")

# 2) Initialize LLM for query classification
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.0, api_key=api_key)

# 3) Query complexity classifier
def classify_query_complexity(query):
    """Classify query as simple, moderate, or complex based on LLM analysis."""
    classify_prompt = ChatPromptTemplate.from_template(
        """Classify the following query by complexity:
- SIMPLE: factual, single-topic, straightforward (e.g., "What is AI?")
- MODERATE: multi-part, some nuance (e.g., "How does AI differ from ML?")
- COMPLEX: open-ended, comparative, requires synthesis (e.g., "Compare ML, DL, and neural networks in context of modern AI applications")

Query: {query}

Respond with one word: SIMPLE, MODERATE, or COMPLEX."""
    )
    
    chain = classify_prompt | llm
    result = chain.invoke({"query": query})
    complexity = result.content.strip().upper()
    
    # Validate response
    if complexity not in ["SIMPLE", "MODERATE", "COMPLEX"]:
        complexity = "MODERATE"  # default
    
    return complexity

# 4) Adaptive configuration based on complexity
def get_adaptive_config(complexity):
    """Return adaptive parameters based on query complexity."""
    configs = {
        "SIMPLE": {
            "chunk_size": 800,
            "chunk_overlap": 50,
            "strategy": "similarity",
            "k": 2,
            "temp": 0.3,
            "description": "Large chunks, single strategy, few results (fast & focused)"
        },
        "MODERATE": {
            "chunk_size": 500,
            "chunk_overlap": 100,
            "strategy": "similarity",
            "k": 4,
            "temp": 0.5,
            "description": "Medium chunks, single strategy, moderate results (balanced)"
        },
        "COMPLEX": {
            "chunk_size": 300,
            "chunk_overlap": 100,
            "strategy": "mmr",
            "k": 6,
            "fetch_k": 20,
            "temp": 0.7,
            "description": "Small chunks, MMR for diversity, many results (comprehensive)"
        }
    }
    return configs.get(complexity, configs["MODERATE"])

# 5) Build vector stores with different chunk sizes
print("Building adaptive vector stores...\n")
stores = {}
for complexity, config in [("SIMPLE", 800), ("MODERATE", 500), ("COMPLEX", 300)]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=config, chunk_overlap=50)
    chunks = splitter.split_text(text)
    
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    db_path = f"./chroma_adaptive_rag_db_{complexity.lower()}"
    try:
        from shutil import rmtree
        if os.path.exists(db_path):
            rmtree(db_path)
    except Exception:
        pass
    
    vectordb = Chroma.from_texts(chunks, embedding=embeddings, persist_directory=db_path, collection_name=f"adaptive_{complexity.lower()}")
    stores[complexity] = vectordb
    print(f"  {complexity}: chunk_size={config}, created {len(chunks)} chunks")

print()

# Example queries with different complexities
queries = [
    "What is artificial intelligence?",  # Simple
    "How do neural networks process information?",  # Moderate
    "Compare supervised learning, unsupervised learning, and reinforcement learning in the context of modern AI applications and their limitations."  # Complex
]

for query in queries:
    print("="*80)
    print(f"Query: {query}\n")
    
    # STEP 1: Classify complexity
    print("STEP 1: Classifying Query Complexity")
    complexity = classify_query_complexity(query)
    print(f"  Complexity: {complexity}\n")
    
    # STEP 2: Get adaptive config
    print("STEP 2: Retrieving Adaptive Configuration")
    config = get_adaptive_config(complexity)
    print(f"  Config: {config['description']}")
    print(f"    - Chunk size: {config['chunk_size']}")
    print(f"    - Strategy: {config['strategy']}")
    print(f"    - Num results: {config['k']}\n")
    
    # STEP 3: Adaptive retrieval
    print("STEP 3: Adaptive Retrieval")
    vectordb = stores[complexity]
    
    if config['strategy'] == "similarity":
        retriever = vectordb.as_retriever(
            search_type="similarity",
            search_kwargs={"k": config['k']}
        )
    else:  # mmr
        retriever = vectordb.as_retriever(
            search_type="mmr",
            search_kwargs={"k": config['k'], "fetch_k": config.get('fetch_k', 15)}
        )
    
    retrieved = retriever.invoke(query)
    context = "\n\n".join([d.page_content for d in retrieved])
    print(f"  Retrieved {len(retrieved)} documents.\n")
    
    # STEP 4: Adaptive generation
    print("STEP 4: Generating Answer with Adaptive Temperature")
    answer_prompt = ChatPromptTemplate.from_template(
        """Answer the question based on the provided context. Be concise and accurate.
Context: {context}
Question: {query}
Answer:"""
    )
    
    adaptive_llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=config['temp'], api_key=api_key)
    chain = answer_prompt | adaptive_llm
    answer = chain.invoke({"context": context[:2000], "query": query})
    
    print("--- Answer ---")
    print(answer.content[:500] + "...\n" if len(answer.content) > 500 else answer.content + "\n")

print("="*80)
print("Adaptive RAG run complete.")

