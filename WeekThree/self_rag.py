from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WikipediaLoader
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import OllamaLLM

# Load and split documents
print("Loading document...")
loader = WikipediaLoader("Python (programming language)", lang="en", load_max_docs=1)
documents = loader.load()

if documents:
    text = documents[0].page_content
    splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=30)
    chunks = splitter.split_text(text)
    print(f"Created {len(chunks)} chunks\n")
    
    # Initialize HuggingFace Embeddings
    print("Loading embedding model...")
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    # Create vector store
    print("Building vector store...")
    db = Chroma.from_texts(
        chunks,
        embedding=embeddings,
        persist_directory="./chroma_self_rag_db",
        collection_name="python_docs"
    )
    retriever = db.as_retriever(search_type="similarity", search_kwargs={"k": 3})
    print("Vector store created.\n")
    
    # Initialize Ollama LLM (local)
    print("Loading Ollama LLM...")
    llm = OllamaLLM(model="mistral")  # or "llama2", "neural-chat", etc.
    
    # Self-RAG Pipeline
    query = "What are the key features of Python?"
    print(f"Query: {query}")
    print("="*80 + "\n")
    
    # Step 1: Retrieve relevant documents
    print("STEP 1: Retrieving relevant documents...")
    retrieved_docs = retriever.invoke(query)
    context = "\n\n".join([doc.page_content for doc in retrieved_docs])
    print(f"Retrieved {len(retrieved_docs)} documents.\n")
    
    # Step 2: Evaluate relevance (simplified with LLM)
    relevance_prompt = ChatPromptTemplate.from_template(
        """Are these documents relevant to the query?
        Query: {query}
        Documents: {context}
        Answer with YES or NO and explain briefly."""
    )
    
    relevance_chain = relevance_prompt | llm
    relevance_response = relevance_chain.invoke({"query": query, "context": context[:500]})
    print("STEP 2: Relevance Check")
    print(relevance_response)
    print()
    
    # Step 3: Generate answer using retrieved context
    rag_prompt = ChatPromptTemplate.from_template(
        """Answer the question based on the provided context.
        Context: {context}
        Question: {query}
        Answer:"""
    )
    
    rag_chain = rag_prompt | llm
    answer = rag_chain.invoke({"query": query, "context": context})
    print("STEP 3: Generated Answer")
    print(answer)
    print()
    
    # Step 4: Self-evaluate answer quality
    evaluation_prompt = ChatPromptTemplate.from_template(
        """Evaluate if this answer is grounded in the provided context.
        Context: {context}
        Question: {query}
        Answer: {answer}
        Provide a score (1-5) and brief justification."""
    )
    
    eval_chain = evaluation_prompt | llm
    evaluation = eval_chain.invoke({
        "query": query,
        "context": context[:500],
        "answer": answer[:200]
    })
    print("STEP 4: Answer Evaluation")
    print(evaluation)
    print()
    
    print("="*80)
    print("Self-RAG pipeline complete!")

else:
    print("No documents loaded.")
