from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WikipediaLoader
from langchain_community.vectorstores import Chroma

# Load and split documents
print("Loading document...")
loader = WikipediaLoader("Machine Learning", lang="en", load_max_docs=1)
documents = loader.load()

if documents:
    text = documents[0].page_content
    splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=30)
    chunks = splitter.split_text(text)
    print(f"Created {len(chunks)} chunks\n")
    
    # Initialize HuggingFace Embeddings
    print("Loading HuggingFace embedding model...")
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    # Create Chroma vector store
    print("Building Chroma vector store...")
    db = Chroma.from_texts(
        chunks,
        embedding=embeddings,
        persist_directory="./chroma_retriever_db",
        collection_name="ml_documents"
    )
    print("Vector store created.\n")
    
    # Convert vector store to retriever
    retriever = db.as_retriever(search_type="similarity", search_kwargs={"k": 3})
    print("Retriever created from vector store.\n")
    
    # Example 1: Basic retrieval
    query = "What is supervised learning?"
    print(f"Query: {query}")
    print("="*80)
    retrieved_docs = retriever.invoke(query)
    
    print(f"Retrieved {len(retrieved_docs)} documents:\n")
    for i, doc in enumerate(retrieved_docs):
        print(f"Document {i + 1}:")
        print(doc.page_content[:250])
        print()
    
    # Example 2: Retriever with MMR (Maximal Marginal Relevance)
    print("="*80)
    print("Using MMR retriever (diversity-aware):\n")
    mmr_retriever = db.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 3, "fetch_k": 10}  # fetch_k > k for diversity
    )
    mmr_docs = mmr_retriever.invoke(query)
    for i, doc in enumerate(mmr_docs):
        print(f"MMR Document {i + 1}:")
        print(doc.page_content[:250])
        print()
    
    # Example 3: Similarity with score threshold
    print("="*80)
    print("Using similarity with score threshold:\n")
    threshold_retriever = db.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={"k": 5, "score_threshold": 0.5}
    )
    threshold_docs = threshold_retriever.invoke(query)
    print(f"Retrieved {len(threshold_docs)} documents above threshold:")
    for i, doc in enumerate(threshold_docs):
        print(f"Document {i + 1}: {doc.page_content[:200]}...\n")

else:
    print("No documents loaded.")
