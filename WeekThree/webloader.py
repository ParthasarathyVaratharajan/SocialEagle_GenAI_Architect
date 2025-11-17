from langchain_community.document_loaders import WebBaseLoader

# Specify the URL(s) to load
urls = [
    "https://www.dailythanthi.com/",  # Replace with your target URL
]

# Initialize the WebBaseLoader
loader = WebBaseLoader(urls)

# Load the document(s)
documents = loader.load()

# Print the loaded content
print(f"Total documents loaded: {len(documents)}\n")
for i, doc in enumerate(documents):
    print(f"--- Document {i + 1} ---")
    print("Source:", doc.metadata.get("source"))
    print("Content:\n", doc.page_content[:500])  # Print first 500 chars
    print("Full Metadata:", doc.metadata)
    print()
