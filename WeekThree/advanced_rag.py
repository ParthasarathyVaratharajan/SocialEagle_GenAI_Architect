import os
from typing import List
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WikipediaLoader, ArxivLoader
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

# Advanced RAG sample
# - Fusion retrieval (similarity + mmr)
# - Iterative refinement: generate -> self-critique -> re-retrieve -> refine
# - Uses Chroma (persistent) + HuggingFace embeddings + OpenAI LLM

# Ensure OPENAI_API_KEY is set
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable not set. Set it before running the script.")

# ---------- Loaders & Splitter ----------
print("Loading source documents...")
wiki_loader = WikipediaLoader("Artificial intelligence", lang="en", load_max_docs=1)
arxiv_loader = ArxivLoader(query="artificial intelligence", load_max_docs=2)

raw_docs = []
for loader in (wiki_loader, arxiv_loader):
    try:
        docs = loader.load()
        for d in docs:
            raw_docs.append(d.page_content)
    except Exception as e:
        print(f"Warning: loader failed: {e}")

if not raw_docs:
    raise SystemExit("No documents loaded. Update loaders or network access.")

splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
chunks: List[str] = []
for text in raw_docs:
    chunks.extend(splitter.split_text(text))

print(f"Total chunks created: {len(chunks)}")

# ---------- Embeddings & Vector Store ----------
print("Initializing embeddings and Chroma vector store...")
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
db_path = "./chroma_advanced_rag_db"

# remove existing db for a clean run (optional)
try:
    from shutil import rmtree
    if os.path.exists(db_path):
        rmtree(db_path)
except Exception:
    pass

vectordb = Chroma.from_texts(chunks, embedding=embeddings, persist_directory=db_path, collection_name="advanced_rag")

# ---------- Retriever strategies (fusion) ----------
retriever_sim = vectordb.as_retriever(search_type="similarity", search_kwargs={"k": 4})
retriever_mmr = vectordb.as_retriever(search_type="mmr", search_kwargs={"k": 4, "fetch_k": 16})

# helper to merge/deduplicate doc list
def merge_dedup(docs_lists: List[List]):
    seen = set()
    merged = []
    for docs in docs_lists:
        for d in docs:
            key = d.page_content[:200]
            if key not in seen:
                seen.add(key)
                merged.append(d)
    return merged

# ---------- LLM and prompts ----------
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.0, api_key=api_key)

initial_prompt = ChatPromptTemplate.from_template(
    """You are an assistant that answers a question using the provided context. Be concise and cite which context paragraphs you used.
Context: {context}
Question: {query}
Answer:"""
)

critique_prompt = ChatPromptTemplate.from_template(
    """Critique the following answer for factual grounding against the context. List any unsupported claims.
Context: {context}
Question: {query}
Answer: {answer}

Respond with: SUPPORTED or UNSUPPORTED, and a short note."""
)

refine_prompt = ChatPromptTemplate.from_template(
    """Refine the answer using the expanded context. If the previous answer had unsupported claims, correct them and mark corrections.
Expanded Context: {context}
Original Answer: {answer}
Question: {query}
Refined Answer:"""
)

# ---------- Pipeline ----------
def fusion_retrieve(query: str):
    docs1 = retriever_sim.invoke(query)
    docs2 = retriever_mmr.invoke(query)
    merged = merge_dedup([docs1, docs2])
    return merged


def generate_answer(context: str, query: str):
    chain = initial_prompt | llm
    out = chain.invoke({"context": context, "query": query})
    return out.content


def critique_answer(context: str, query: str, answer: str):
    chain = critique_prompt | llm
    out = chain.invoke({"context": context, "query": query, "answer": answer})
    return out.content


def refine_answer(expanded_context: str, query: str, answer: str):
    chain = refine_prompt | llm
    out = chain.invoke({"context": expanded_context, "query": query, "answer": answer})
    return out.content


# Example query
query = "How does self-supervised learning differ from supervised learning, and where is it useful?"
print(f"Query: {query}\n")

# 1) Fusion retrieval
retrieved = fusion_retrieve(query)
print(f"Retrieved {len(retrieved)} fused documents (deduplicated).\n")

# Prepare initial context (top N)
context = "\n\n".join([d.page_content for d in retrieved[:6]])

# 2) Initial answer
answer = generate_answer(context, query)
print("Initial Answer:\n", answer, "\n")

# 3) Self-critique
critique = critique_answer(context, query, answer)
print("Critique:\n", critique, "\n")

# If critique finds unsupported claims, re-retrieve with expanded query
if "UNSUPPORTED" in critique.upper():
    print("Unsupported claims detected — performing corrective re-retrieval...\n")
    # create an expansion query to fetch complementary docs
    expansion_query = query + " additional details limitations examples"
    more_docs = fusion_retrieve(expansion_query)
    # merge with previous retrieved docs, keep unique
    merged_docs = merge_dedup([retrieved, more_docs])
    expanded_context = "\n\n".join([d.page_content for d in merged_docs[:10]])
    # 4) Refine answer
    refined = refine_answer(expanded_context, query, answer)
    print("Refined Answer:\n", refined, "\n")
else:
    print("Answer appears supported by the context — no refinement needed.\n")

print("Advanced RAG pipeline complete.")
