import os
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WikipediaLoader
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

# Check for OpenAI API key
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable not set.")

# Load and split documents
print("Loading document...")
loader = WikipediaLoader("Machine Learning", lang="en", load_max_docs=1)
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
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7, api_key=api_key)
    
    # Corrective RAG Pipeline
    query = "What is transfer learning in machine learning?"
    print(f"Query: {query}")
    print("="*80 + "\n")
    
    # Step 1: Initial Retrieval
    print("STEP 1: Initial Retrieval")
    retrieved_docs = retriever.invoke(query)
    context = "\n\n".join([doc.page_content for doc in retrieved_docs])
    print(f"Retrieved {len(retrieved_docs)} documents.\n")
    
    # Step 2: Evaluate Retrieved Documents
    print("STEP 2: Evaluating Document Relevance")
    relevance_prompt = ChatPromptTemplate.from_template(
        """Evaluate if these documents are relevant to answer the query.
        Query: {query}
        Documents: {context}
        
        Respond with:
        - RELEVANT: if documents contain useful information
        - NOT_RELEVANT: if documents don't address the query
        
        Brief explanation (1 sentence)."""
    )
    
    relevance_chain = relevance_prompt | llm
    relevance_response = relevance_chain.invoke({"query": query, "context": context[:500]})
    relevance_text = relevance_response.content
    print(relevance_text)
    print()
    
    # Step 3: Conditional Logic - Correct if Not Relevant
    if "NOT_RELEVANT" in relevance_text.upper():
        print("STEP 3: Documents Not Relevant - Re-retrieving with different strategy")
        # Re-retrieve with MMR (Maximal Marginal Relevance) for diversity
        mmr_retriever = db.as_retriever(
            search_type="mmr",
            search_kwargs={"k": 5, "fetch_k": 20}
        )
        retrieved_docs = mmr_retriever.invoke(query)
        context = "\n\n".join([doc.page_content for doc in retrieved_docs])
        print(f"Re-retrieved {len(retrieved_docs)} documents using MMR.\n")
    else:
        print("STEP 3: Documents are relevant - proceeding with generation\n")
    
    # Step 4: Generate Answer
    print("STEP 4: Generating Answer")
    rag_prompt = ChatPromptTemplate.from_template(
        """Answer the question based on the provided context. Be detailed and accurate.
        Context: {context}
        Question: {query}
        Answer:"""
    )
    
    rag_chain = rag_prompt | llm
    answer = rag_chain.invoke({"query": query, "context": context})
    print(answer.content)
    print()
    
    # Step 5: Evaluate Answer Quality
    print("STEP 5: Evaluating Answer Quality")
    evaluation_prompt = ChatPromptTemplate.from_template(
        """Evaluate if this answer is grounded in the context and answers the question well.
        Context: {context}
        Question: {query}
        Answer: {answer}
        
        Score (1-5) and reason:"""
    )
    
    eval_chain = evaluation_prompt | llm
    evaluation = eval_chain.invoke({
        "query": query,
        "context": context[:500],
        "answer": answer.content[:300]
    })
    print(evaluation.content)
    print()
    
    print("="*80)
    print("Corrective RAG pipeline complete!")

else:
    print("No documents loaded.")
