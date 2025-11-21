import streamlit as st
import re
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WikipediaLoader
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

# Page config
st.set_page_config(page_title="RAG Chatbot", layout="wide", initial_sidebar_state="expanded")
st.title("🤖 RAG Chatbot")
st.markdown("Ask questions about AI and Machine Learning using Retrieval-Augmented Generation")

# Sidebar: Configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("OpenAI API Key", type="password", help="Required for question answering")
    
    topic = st.selectbox(
        "Knowledge Base Topic",
        ["Artificial Intelligence", "Machine Learning", "Deep Learning", "Python"],
        help="Select topic to load Wikipedia documents"
    )
    
    retrieval_type = st.selectbox(
        "Retrieval Strategy",
        ["similarity", "mmr"],
        help="Similarity: fast, relevant | MMR: diverse results"
    )
    
    num_results = st.slider("Number of Retrieved Docs", 1, 10, 4, help="More docs = slower but more context")

# Initialize session state
if "vectordb" not in st.session_state:
    st.session_state.vectordb = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "initialized" not in st.session_state:
    st.session_state.initialized = False

# Main area: Two columns
col1, col2 = st.columns([2, 1], gap="medium")

with col1:
    st.subheader("💬 Chat")
    
    # Display chat history
    chat_container = st.container(height=400, border=True)
    with chat_container:
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

with col2:
    st.subheader("📚 Knowledge Base")
    
    if not st.session_state.initialized and api_key:
        with st.spinner(f"Loading {topic} knowledge base..."):
            try:
                # Load Wikipedia documents
                loader = WikipediaLoader(topic, lang="en", load_max_docs=1)
                docs = loader.load()
                
                if docs:
                    text = docs[0].page_content
                    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
                    chunks = splitter.split_text(text)
                    
                    # Create embeddings and vector store
                    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
                    # sanitize topic to a valid collection name (allowed: a-zA-Z0-9._-)
                    safe_topic = re.sub(r'[^a-zA-Z0-9._-]+', '_', topic.lower()).strip('_')
                    db_path = f"./chroma_rag_chatbot_{safe_topic}"
                    st.session_state.vectordb = Chroma.from_texts(
                        chunks,
                        embedding=embeddings,
                        persist_directory=db_path,
                        collection_name=f"rag_{safe_topic}"
                    )
                    st.session_state.initialized = True
                    st.success(f"✅ Loaded {len(chunks)} chunks from {topic}")
                else:
                    st.error("Failed to load documents")
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    if st.session_state.initialized:
        st.info(f"✓ Ready with {topic}")
    elif not api_key:
        st.warning("Enter OpenAI API Key to get started")

# Input area: Question
st.divider()
user_input = st.chat_input("Ask a question about the knowledge base...", disabled=not (st.session_state.initialized and api_key))

if user_input:
    # Add user message to history
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    
    # Retrieve documents
    if st.session_state.vectordb:
        retriever = st.session_state.vectordb.as_retriever(
            search_type=retrieval_type,
            search_kwargs={"k": num_results} if retrieval_type == "similarity" else {"k": num_results, "fetch_k": num_results * 3}
        )
        retrieved_docs = retriever.invoke(user_input)
        context = "\n\n".join([d.page_content for d in retrieved_docs])
        
        # Generate answer
        with st.spinner("Generating answer..."):
            try:
                llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.0, api_key=api_key)
                answer_prompt = ChatPromptTemplate.from_template(
                    """Answer the question based on the provided context. If the context doesn't contain the answer, say "I don't have enough information in my knowledge base to answer this."
Context: {context}
Question: {query}
Answer:"""
                )
                chain = answer_prompt | llm
                result = chain.invoke({"context": context[:2000], "query": user_input})
                answer = result.content
                
                # Add assistant message to history
                st.session_state.chat_history.append({"role": "assistant", "content": answer})
                
                # Show answer with sources
                st.chat_message("assistant").write(answer)
                
                # Show retrieved documents
                with st.expander("📖 Retrieved Documents"):
                    for i, doc in enumerate(retrieved_docs, 1):
                        st.markdown(f"**Document {i}**")
                        st.text(doc.page_content[:300] + "..." if len(doc.page_content) > 300 else doc.page_content)
                        st.divider()
            except Exception as e:
                st.error(f"Error generating answer: {str(e)}")
    else:
        st.error("Knowledge base not initialized")

# Footer
st.divider()
st.caption("🔍 RAG Chatbot using LangChain, Chroma, HuggingFace, and OpenAI | Data from Wikipedia")
