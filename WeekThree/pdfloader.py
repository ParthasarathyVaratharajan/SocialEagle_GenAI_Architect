from langchain_community.document_loaders import PyPDFLoader

# Specify the path to your PDF file
file_path = "sample.pdf"

# Initialize the PyPDFLoader
loader = PyPDFLoader(file_path)

# Load the document
documents = loader.load()

# Print the loaded content
print(f"Total pages loaded: {len(documents)}\n")
for i, doc in enumerate(documents):
    print(f"--- Page {i + 1} ---")
    print("Document Content:\n", doc.page_content)
    print("Metadata:", doc.metadata)
    print()
