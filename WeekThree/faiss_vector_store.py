from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WikipediaLoader
from langchain_community.vectorstores import FAISS

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
    
    # Create FAISS vector store from text chunks
    print("Building FAISS vector store...")
    db = FAISS.from_texts(chunks, embedding=embeddings)
    print("FAISS store created.")
    
    # Example: similarity search
    query = "What is artificial intelligence?"
    print(f"\nSearching for: {query}")
    results = db.similarity_search(query, k=3)
    for i, doc in enumerate(results):
        print(f"\nResult {i + 1}:")
        print(doc.page_content[:300])
else:
    print("No documents loaded.")
