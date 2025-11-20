from langchain_text_splitters import CharacterTextSplitter

# Sample long text
long_text = """
LangChain is a powerful framework for building applications with language models.
Text splitting is essential when working with large documents to ensure they fit within the model's context window.
This example demonstrates how to split text using CharacterTextSplitter.
"""

# Initialize the splitter
splitter = CharacterTextSplitter(
    separator="\n",        # Split on newline characters
    chunk_size=100,        # Max characters per chunk
    chunk_overlap=20       # Overlap between chunks
)

# Split the text
chunks = splitter.split_text(long_text)

# Display the chunks
for i, chunk in enumerate(chunks):
    print(f"\nChunk {i+1}:\n{chunk}")