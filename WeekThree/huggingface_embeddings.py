from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WikipediaLoader

# Load and split documents
print("Loading document...")
loader = WikipediaLoader("Artificial Intelligence", lang="en", load_max_docs=1)
documents = loader.load()

if documents:
    text = documents[0].page_content
    
    # Split text into chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=30,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = splitter.split_text(text)
    print(f"Created {len(chunks)} chunks\n")
    
    # Initialize HuggingFace Embeddings
    # Using a lightweight model for fast processing
    print("Loading HuggingFace embedding model...")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    
    # Embed the first few chunks
    print("Embedding first 3 chunks...\n")
    for i, chunk in enumerate(chunks[:3]):
        embedding = embeddings.embed_query(chunk)
        print(f"Chunk {i + 1}:")
        print(f"  Text preview: {chunk[:60]}...")
        print(f"  Embedding dimension: {len(embedding)}")
        print(f"  First 5 values: {embedding[:5]}")
        print()
    
    # Compute similarity between two chunks (optional)
    if len(chunks) >= 2:
        print("Computing similarity between chunk 1 and chunk 2...")
        emb1 = embeddings.embed_query(chunks[0])
        emb2 = embeddings.embed_query(chunks[1])
        
        # Simple cosine similarity
        import numpy as np
        dot_product = np.dot(emb1, emb2)
        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)
        similarity = dot_product / (norm1 * norm2)
        print(f"Cosine similarity: {similarity:.4f}")
else:
    print("No documents loaded.")
