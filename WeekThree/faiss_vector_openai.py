from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from openai import api_key
import os

# Step 1: Load your document
loader = TextLoader("sample.txt")  # Replace with your file path
documents = loader.load()

# Step 2: Split into chunks
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = splitter.split_documents(documents)

# Step 3: Embed chunks
api_key_value = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable not set. Set it before running the script.")

embedding_model = OpenAIEmbeddings(model="text-embedding-ada-002",api_key=api_key_value)  # Requires OpenAI API key

# Step 4: Store in FAISS vector store
vector_store = FAISS.from_documents(chunks, embedding_model)

# Step 5: Perform semantic search
query = "What is LangChain?"
results = vector_store.similarity_search(query, k=3)

# Step 6: Display results
for i, doc in enumerate(results):
    print(f"\nResult {i+1}:\n{doc.page_content}")