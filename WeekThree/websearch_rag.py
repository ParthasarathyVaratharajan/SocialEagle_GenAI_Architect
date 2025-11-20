import os
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WikipediaLoader
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_community.tools import DuckDuckGoSearchRun

# Web Search RAG sample
# - Retrieve from local knowledge base (vector store)
# - Augment with live web search results for real-time information
# - Combine local + web context for comprehensive, up-to-date answers
# - Uses DuckDuckGo for web search (no API key required)

# Require OPENAI_API_KEY
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable not set. Set it before running the script.")

# 1) Load documents and build local knowledge base
print("Building local knowledge base...")
loader = WikipediaLoader("Machine learning", lang="en", load_max_docs=1)
docs = loader.load()
if not docs:
    raise SystemExit("No documents loaded. Check network or loader settings.")

text = docs[0].page_content
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = splitter.split_text(text)
print(f"Created {len(chunks)} chunks from local source.\n")

# 2) Build embeddings + Chroma vector store
print("Building Chroma vector store...")
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
db_path = "./chroma_websearch_rag_db"
try:
    from shutil import rmtree
    if os.path.exists(db_path):
        rmtree(db_path)
except Exception:
    pass

vectordb = Chroma.from_texts(chunks, embedding=embeddings, persist_directory=db_path, collection_name="websearch_rag")
local_retriever = vectordb.as_retriever(search_type="similarity", search_kwargs={"k": 4})

# 3) Initialize web search tool (DuckDuckGo - no API key needed)
print("Initializing web search tool (DuckDuckGo)...\n")
web_search = DuckDuckGoSearchRun()

# 4) Initialize LLM
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.0, api_key=api_key)

# Example query
query = "What are the latest trends in machine learning in 2024?"
print(f"Query: {query}\n")
print("="*80 + "\n")

# STEP 1: Local retrieval
print("STEP 1: Retrieving from Local Knowledge Base")
local_docs = local_retriever.invoke(query)
local_context = "\n\n".join([d.page_content for d in local_docs[:4]])
print(f"Retrieved {len(local_docs)} documents from local KB.\n")

# STEP 2: Web search
print("STEP 2: Performing Web Search for Real-Time Information")
print(f"Searching: '{query}'...")
try:
    web_results = web_search.run(query)
    print("Web search results obtained.\n")
except Exception as e:
    print(f"Web search failed: {e}. Proceeding with local knowledge only.\n")
    web_results = None

# STEP 3: Combine contexts
print("STEP 3: Fusing Local and Web Contexts")
if web_results:
    fused_context = f"""Local Knowledge Base:
{local_context}

Web Search Results:
{web_results}"""
    source = "local + web"
else:
    fused_context = local_context
    source = "local only"

print(f"Fused context source: {source}\n")

# STEP 4: Generate answer with combined context
print("STEP 4: Generating Answer")
answer_prompt = ChatPromptTemplate.from_template(
    """You are an assistant that answers questions using both local knowledge and real-time web information.
Provide a comprehensive, up-to-date answer.

Context (from local KB and web search):
{context}

Question: {query}

Answer:"""
)

answer_chain = answer_prompt | llm
answer = answer_chain.invoke({"context": fused_context[:3000], "query": query})
print("--- Answer (Local + Web) ---\n")
print(answer.content)
print()

# STEP 5: Generate citation/source info
print("STEP 5: Source Attribution")
citation_prompt = ChatPromptTemplate.from_template(
    """Based on the answer provided, identify which claims came from local knowledge vs web search results.
Answer: {answer}
Question: {query}

Attribution:"""
)

citation_chain = citation_prompt | llm
citation = citation_chain.invoke({"answer": answer.content, "query": query})
print(citation.content)
print()

print("="*80)
print("Web Search RAG run complete.")
