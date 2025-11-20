import os
from typing import List
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WikipediaLoader
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

# Speculative RAG sample
# 1) Generate an answer that may contain speculation (explicitly labeled)
# 2) Extract speculative claims from the answer
# 3) Verify each speculative claim by retrieving supporting docs

# Require OPENAI_API_KEY
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable not set. Set it (PowerShell or cmd) before running.")

# Load source documents (Wikipedia example)
loader = WikipediaLoader("Artificial intelligence", lang="en", load_max_docs=1)
docs = loader.load()
if not docs:
    raise SystemExit("No documents loaded. Check network or loader settings.")

text = docs[0].page_content
splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
chunks: List[str] = splitter.split_text(text)
print(f"Created {len(chunks)} chunks from source.\n")

# Build Chroma vector store
db_path = "./chroma_speculative_rag_db"
# remove previous db for a clean run (optional)
try:
    from shutil import rmtree
    if os.path.exists(db_path):
        rmtree(db_path)
except Exception:
    pass

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vectordb = Chroma.from_texts(chunks, embedding=embeddings, persist_directory=db_path, collection_name="speculative")
retriever = vectordb.as_retriever(search_type="similarity", search_kwargs={"k": 5})

# Initialize LLM
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7, api_key=api_key)

# Prompts
speculative_prompt = ChatPromptTemplate.from_template(
    """Answer the question using the provided context. If you must hypothesize or extrapolate beyond the context, include a separate section labeled 'Speculation' and explicitly mark each speculative claim.
Context: {context}
Question: {query}

Answer (include a short 'Speculation' section if needed):"""
)

extract_claims_prompt = ChatPromptTemplate.from_template(
    """Extract a numbered list of speculative claims from the Speculation section of the answer. If there is no speculation section, respond with 'NONE'.

Answer: {answer}

Speculative claims:"""
)

verify_prompt = ChatPromptTemplate.from_template(
    """For the claim "{claim}", search the provided documents (context) and say whether it is SUPPORTED, CONTRADICTED, or NOT_FOUND. Give a short justification and list any source titles/URLs you used.
Context snippets (first 1000 chars): {context}

Verification:"""
)

# Query
query = "Will AI agents replace software developers in ten years?"
print(f"Query: {query}\n")

# 1) Retrieve context and generate speculative answer
ctx_docs = retriever.invoke(query)
context = "\n\n".join([d.page_content for d in ctx_docs[:6]])

spec_chain = speculative_prompt | llm
spec_out = spec_chain.invoke({"context": context, "query": query})
answer_text = spec_out.content
print("--- Speculative Answer ---\n")
print(answer_text[:2000], "\n")

# 2) Extract speculative claims
extract_chain = extract_claims_prompt | llm
claims_out = extract_chain.invoke({"answer": answer_text})
claims_text = claims_out.content.strip()
print("--- Extracted Claims ---\n")
print(claims_text, "\n")

claims = []
if claims_text.upper() != "NONE":
    # parse numbered lines
    for line in claims_text.splitlines():
        line = line.strip()
        if not line:
            continue
        # remove leading numbering like '1.' or '-'
        if line[0].isdigit():
            # split at first '.'
            parts = line.split('.', 1)
            if len(parts) > 1:
                claim = parts[1].strip()
            else:
                claim = line
        elif line.startswith('-'):
            claim = line[1:].strip()
        else:
            claim = line
        claims.append(claim)

# 3) Verify each claim by retrieval
if not claims:
    print("No speculative claims to verify.\n")
else:
    print("--- Verification Report ---\n")
    for i, claim in enumerate(claims, 1):
        print(f"Claim {i}: {claim}\n")
        # retrieve for the claim
        support_docs = retriever.invoke(claim)
        support_text = "\n\n".join([d.page_content for d in support_docs[:6]])
        # create verify prompt using limited context snippet
        verify_chain = verify_prompt | llm
        vout = verify_chain.invoke({"claim": claim, "context": support_text[:1000]})
        print(vout.content)
        print("-"*60)

print("Speculative RAG run complete.")
