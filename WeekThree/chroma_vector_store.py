from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WikipediaLoader
from langchain_community.vectorstores import Chroma
import os
import shutil

# Load and split documents
print("Loading document...")
loader = WikipediaLoader("Artificial Intelligence", lang="en", load_max_docs=1)
documents = loader.load()

if documents:
    text = documents[0].page_content
    splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=30)
    chunks = splitter.split_text(text)
    print(f"Created {len(chunks)} chunks\n")
    
    # Initialize HuggingFace Embeddings
    print("Loading HuggingFace embedding model...")
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    # Create Chroma vector store from text chunks
    # Chroma stores data in a persistent directory
    db_path = "./chroma_db"
    
    # Clean up old database if it exists (optional)
    if os.path.exists(db_path):
        shutil.rmtree(db_path)
    
    print("Building Chroma vector store...")
    db = Chroma.from_texts(
        chunks,
        embedding=embeddings,
        persist_directory=db_path,
        collection_name="ai_documents"
    )
    print(f"Chroma store created at: {db_path}\n")
    
    # Example: similarity search
    query = "What is artificial intelligence?"
    print(f"Searching for: {query}")
    results = db.similarity_search(query, k=3)
    
    for i, doc in enumerate(results):
        print(f"\nResult {i + 1}:")
        print(doc.page_content[:300])
        print(f"[Metadata: {doc.metadata}]")
    
    # Example: similarity search with scores
    print("\n" + "="*80)
    print("Similarity search with scores:")
    results_with_scores = db.similarity_search_with_score(query, k=2)
    for doc, score in results_with_scores:
        print(f"\nScore: {score:.4f}")
        print(doc.page_content[:200])
    
    # Persist the database (already done with persist_directory)
    # db.persist()
    
else:
    print("No documents loaded.")
