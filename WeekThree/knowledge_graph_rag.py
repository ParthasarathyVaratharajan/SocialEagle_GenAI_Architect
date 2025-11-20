import os
import json
import networkx as nx
from typing import List
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WikipediaLoader
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

# Knowledge Graph RAG sample
# - Retrieve relevant docs
# - Use LLM to extract (subject, relation, object) triples
# - Build a simple knowledge graph (networkx)
# - Use the graph to expand retrieval (neighbor entities -> more context)
# - Generate final answer with fused context and graph facts

# Require OPENAI_API_KEY
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable not set. Set it before running the script.")

# 1) Load documents and split
print("Loading source document...")
loader = WikipediaLoader("Knowledge graph", lang="en", load_max_docs=1)
docs = loader.load()
if not docs:
    raise SystemExit("No documents loaded. Check network or loader settings.")

text = docs[0].page_content
splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
chunks: List[str] = splitter.split_text(text)
print(f"Created {len(chunks)} chunks from source.\n")

# 2) Build embeddings + vector store (Chroma)
print("Building embeddings and Chroma vector store...")
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
db_path = "./chroma_kg_rag_db"
# remove previous db for a clean run (optional)
try:
    from shutil import rmtree
    if os.path.exists(db_path):
        rmtree(db_path)
except Exception:
    pass

vectordb = Chroma.from_texts(chunks, embedding=embeddings, persist_directory=db_path, collection_name="kg_rag")
retriever = vectordb.as_retriever(search_type="similarity", search_kwargs={"k": 5})

# 3) Initialize LLM for triple extraction and answers
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.0, api_key=api_key)

triple_extraction_prompt = ChatPromptTemplate.from_template(
    """Extract factual triples from the following text. Return a JSON array of objects with keys: subject, relation, object.
Text: {text}
Only return valid JSON. Example: [{{\"subject\": \"S\", \"relation\": \"R\", \"object\": \"O\"}}]"""
)

# 4) Example query
query = "How are knowledge graphs used in search and retrieval?"
print(f"Query: {query}\n")

# 5) Retrieve initial context
retrieved = retriever.invoke(query)
context = "\n\n".join([d.page_content for d in retrieved[:6]])
print(f"Retrieved {len(retrieved)} documents for initial context.\n")

# 6) Extract triples from the retrieved context
print("Extracting triples from retrieved context via LLM...")
extract_chain = triple_extraction_prompt | llm
extraction = extract_chain.invoke({"text": context[:3000]})
raw = extraction.content.strip()
triples = []
try:
    # Some LLMs return code fences; strip them
    if raw.startswith("```"):
        raw = raw.strip("`\n")
    triples = json.loads(raw)
except Exception:
    # Fallback: try to parse line-based triples
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        # naive split on '|', ',' or '-'
        for sep in ['|', ',', ' - ', ' – '] :
            if sep in line:
                parts = [p.strip().strip('"') for p in line.split(sep)]
                if len(parts) >= 3:
                    triples.append({"subject": parts[0], "relation": parts[1], "object": parts[2]})
                    break

print(f"Extracted {len(triples)} triples.\n")
for t in triples[:10]:
    print(t)
print()

# 7) Build knowledge graph
G = nx.DiGraph()
for t in triples:
    s = t.get("subject")
    r = t.get("relation")
    o = t.get("object")
    if s and o:
        G.add_node(s)
        G.add_node(o)
        G.add_edge(s, o, relation=r)

print(f"Knowledge graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges.\n")

# 8) Use graph to expand retrieval: find entities related to query tokens
tokens = [w.lower() for w in query.split() if len(w) > 3]
candidate_nodes = [n for n in G.nodes if any(tok in n.lower() for tok in tokens)]
print(f"Candidate graph nodes matching query tokens: {candidate_nodes}\n")

# Find neighbors of candidate nodes
expansion_entities = set()
for n in candidate_nodes:
    neighbors = list(G.neighbors(n)) + [p for p, _ in G.in_edges(n)]
    expansion_entities.update(neighbors)

print(f"Expansion entities from KG neighbors: {list(expansion_entities)[:10]}\n")

# 9) Retrieve additional context for expansion entities
expanded_snippets = []
for ent in list(expansion_entities)[:10]:
    # simple retrieval by entity string
    hits = vectordb.similarity_search(ent, k=3)
    for h in hits:
        expanded_snippets.append(h.page_content[:800])

expanded_context = "\n\n".join(expanded_snippets[:10])

# 10) Generate final answer using fused context and top KG facts
kg_facts = []
for u, v, data in G.edges(data=True):
    kg_facts.append(f"{u} -[{data.get('relation')}]-> {v}")
kg_summary = "\n".join(kg_facts[:20])

final_prompt = ChatPromptTemplate.from_template(
    """You are an assistant. Use the provided fused context and the knowledge-graph facts to answer the question concisely.
Question: {query}
Knowledge-Graph-Facts:
{kg}

Fused Context:
{context}

Answer:"""
)

final_chain = final_prompt | llm
fused_context = (context[:2000] + "\n\n" + expanded_context[:2000]).strip()
final_out = final_chain.invoke({"query": query, "kg": kg_summary, "context": fused_context})
print("--- Final Answer (KG-augmented) ---\n")
print(final_out.content)
print() 

print("Knowledge-Graph RAG run complete.")
