from langchain_community.document_loaders import TextLoader

# Specify the path to your text file
file_path = "sample.txt"

# Initialize the TextLoader
loader = TextLoader(file_path)

# Load the document
documents = loader.load()

# Print the loaded content
for doc in documents:
    print("Document Content:\n", doc.page_content)