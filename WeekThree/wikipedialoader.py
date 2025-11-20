from langchain_community.document_loaders import WikipediaLoader
#from yarl import Query

# Example: load specific Wikipedia page titles
titles = [
    "Python (programming language)",
    "Streamlit (software)",
]

# Initialize the loader (language optional)
loader=WikipediaLoader("AI Agents", lang="en", load_max_docs=5)
# Load documents
documents = loader.load()

print(f"Total pages loaded: {len(documents)}\n")
for i, doc in enumerate(documents):
    print(f"--- Page {i + 1} ---")
    # Title is usually available in metadata
    print("Title:", doc.metadata.get("title"))
    print("URL:", doc.metadata.get("source"))
    print("Content preview:\n", doc.page_content[:500])
    print("Full metadata:", doc.metadata)
    print()

# Alternative: search by a query (uncomment to use)
# query_loader = WikipediaLoader(query="streamlit python web app", lang="en", load_max_docs=3)
# query_docs = query_loader.load()
# print(f"Loaded {len(query_docs)} docs from search query")