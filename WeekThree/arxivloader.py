from langchain_community.document_loaders import ArxivLoader

# Specify the ArXiv paper identifier(s) or search query
# You can use arXiv IDs (e.g., "2101.00001") or search queries
arxiv_query = "machine learning"  # Search for papers on machine learning

# Initialize the ArxivLoader
#loader = ArxivLoader(query=arxiv_query, load_max_docs=5)  # Load max 5 papers
loader = ArxivLoader(query="1706.03762", load_max_docs=5)  # Load max 5 papers

# Load the documents
documents = loader.load()

# Print the loaded content
print(f"Total papers loaded: {len(documents)}\n")
for i, doc in enumerate(documents):
    print(f"--- Paper {i + 1} ---")
    print("Title:", doc.metadata.get("title"))
    print("Authors:", doc.metadata.get("authors"))
    print("Published:", doc.metadata.get("Published"))
    print("ArXiv ID:", doc.metadata.get("arxiv_id"))
    print("Summary:\n", doc.page_content[:300])  # Print first 300 chars of summary
    print("Full Metadata:", doc.metadata)
    print()
