from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WikipediaLoader

# Load a document to split
loader = WikipediaLoader("Python (programming language)", lang="en", load_max_docs=1)
documents = loader.load()

if documents:
    text = documents[0].page_content
    print(f"Original text length: {len(text)} characters\n")
    
    # Initialize RecursiveCharacterTextSplitter
    # chunk_size: maximum size of each chunk
    # chunk_overlap: overlap between chunks (helps maintain context)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", " ", ""]  # Try to split on these in order
    )
    
    # Split the text
    chunks = splitter.split_text(text)
    
    print(f"Total chunks created: {len(chunks)}\n")
    print("=" * 80)
    
    # Display each chunk
    for i, chunk in enumerate(chunks[:5]):  # Show first 5 chunks
        print(f"\nChunk {i + 1}:")
        print("-" * 40)
        print(chunk)
        print(f"[Length: {len(chunk)} characters]")
    
    if len(chunks) > 5:
        print(f"\n... and {len(chunks) - 5} more chunks")
else:
    print("No documents loaded.")
