from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WikipediaLoader
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

# Set your OpenAI API key before running:
# export OPENAI_API_KEY="your-api-key-here"  (Linux/Mac)
# set OPENAI_API_KEY=your-api-key-here       (Windows)

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
    
    # Create FAISS vector store
    print("Building FAISS vector store...")
    db = FAISS.from_texts(chunks, embedding=embeddings)
    retriever = db.as_retriever(search_type="similarity", search_kwargs={"k": 3})
    print("FAISS vector store created.\n")
    
    # Initialize OpenAI LLM
    print("Loading OpenAI ChatGPT...")
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7)
    
    # Self-RAG Pipeline
    query = "What are the key features and advantages of Python?"
    print(f"Query: {query}")
    print("="*80 + "\n")
    
    # Step 1: Retrieve relevant documents
    print("STEP 1: Retrieving relevant documents...")
    retrieved_docs = retriever.invoke(query)
    context = "\n\n".join([doc.page_content for doc in retrieved_docs])
    print(f"Retrieved {len(retrieved_docs)} documents.\n")
    print("Context preview:")
    print(context[:300] + "...\n")
    
    # Step 2: Evaluate relevance
    relevance_prompt = ChatPromptTemplate.from_template(
        """Are these documents relevant to the query?
        Query: {query}
        Documents: {context}
        Answer with YES or NO and explain briefly (1-2 sentences)."""
    )
    
    relevance_chain = relevance_prompt | llm
    relevance_response = relevance_chain.invoke({"query": query, "context": context[:500]})
    print("STEP 2: Relevance Check")
    print(relevance_response.content)
    print()
    
    # Step 3: Generate answer using retrieved context
    rag_prompt = ChatPromptTemplate.from_template(
        """Answer the question based on the provided context. Be concise and clear.
        Context: {context}
        Question: {query}
        Answer:"""
    )
    
    rag_chain = rag_prompt | llm
    answer = rag_chain.invoke({"query": query, "context": context})
    print("STEP 3: Generated Answer")
    print(answer.content)
    print()
    
    # Step 4: Self-evaluate answer quality
    evaluation_prompt = ChatPromptTemplate.from_template(
        """Evaluate if this answer is grounded in the provided context and accurate.
        Context: {context}
        Question: {query}
        Answer: {answer}
        Provide a score (1-5) where 5 is fully grounded and accurate."""
    )
    
    eval_chain = evaluation_prompt | llm
    evaluation = eval_chain.invoke({
        "query": query,
        "context": context[:500],
        "answer": answer.content[:300]
    })
    print("STEP 4: Answer Evaluation")
    print(evaluation.content)
    print()
    
    print("="*80)
    print("Self-RAG pipeline with FAISS + OpenAI complete!")

else:
    print("No documents loaded.")
