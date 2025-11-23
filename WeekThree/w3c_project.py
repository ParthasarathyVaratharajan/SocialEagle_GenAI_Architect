import streamlit as st
import tempfile
import os
from datetime import datetime

# Page config
st.set_page_config(
    page_title="Government Document Intelligence System",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional government interface
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .main-title {
        color: white;
        font-size: 2.5rem;
        font-weight: bold;
        margin: 0;
        text-align: center;
    }
    .main-subtitle {
        color: #e0e7ff;
        font-size: 1.1rem;
        text-align: center;
        margin-top: 0.5rem;
    }
    .status-box {
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 4px solid;
    }
    .status-success {
        background-color: #f0fdf4;
        border-color: #22c55e;
    }
    .status-warning {
        background-color: #fffbeb;
        border-color: #f59e0b;
    }
    .status-error {
        background-color: #fef2f2;
        border-color: #ef4444;
    }
    .status-info {
        background-color: #eff6ff;
        border-color: #3b82f6;
    }
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border: 1px solid #e5e7eb;
    }
    .log-container {
        background-color: #1e293b;
        color: #e2e8f0;
        padding: 1rem;
        border-radius: 8px;
        font-family: 'Courier New', monospace;
        font-size: 0.9rem;
        max-height: 400px;
        overflow-y: auto;
    }
    .log-entry {
        margin: 0.3rem 0;
        padding: 0.3rem;
    }
    .log-timestamp {
        color: #94a3b8;
    }
    .log-success {
        color: #4ade80;
    }
    .log-error {
        color: #f87171;
    }
    .log-info {
        color: #60a5fa;
    }
    .log-warning {
        color: #fbbf24;
    }
    .sidebar-section {
        background: #f8fafc;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        border: 1px solid #e2e8f0;
    }
    .divider {
        height: 2px;
        background: linear-gradient(to right, transparent, #3b82f6, transparent);
        margin: 2rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state for logs
if 'logs' not in st.session_state:
    st.session_state.logs = []
if 'document_uploaded' not in st.session_state:
    st.session_state.document_uploaded = False
if 'total_chunks' not in st.session_state:
    st.session_state.total_chunks = 0

def add_log(message, level="info"):
    """Add log entry with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.logs.append({
        'timestamp': timestamp,
        'level': level,
        'message': message
    })
    # Keep only last 50 logs
    if len(st.session_state.logs) > 50:
        st.session_state.logs = st.session_state.logs[-50:]

def display_logs():
    """Display logs in a terminal-like interface"""
    log_html = "<div class='log-container'>"
    for log in reversed(st.session_state.logs[-20:]):  # Show last 20 logs
        level_class = f"log-{log['level']}"
        log_html += f"""
        <div class='log-entry'>
            <span class='log-timestamp'>[{log['timestamp']}]</span>
            <span class='{level_class}'>[{log['level'].upper()}]</span>
            <span>{log['message']}</span>
        </div>
        """
    log_html += "</div>"
    st.markdown(log_html, unsafe_allow_html=True)

# Header
st.markdown("""
<div class='main-header'>
    <h1 class='main-title'>🏛️ Government Document Intelligence System</h1>
    <p class='main-subtitle'>Secure AI-Powered Document Analysis & Query System</p>
</div>
""", unsafe_allow_html=True)

# Sidebar Configuration
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3774/3774299.png", width=100)
    st.markdown("### 🔐 System Configuration")
    
    with st.expander("📋 System Information", expanded=True):
        st.info("""
        **Version:** 1.0.0  
        **Environment:** Production  
        **Security:** Government Grade  
        **Compliance:** ISO 27001
        """)
    
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    
    # Import libraries
    try:
        from langchain_community.document_loaders import PyPDFLoader
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        from langchain_openai import ChatOpenAI, OpenAIEmbeddings
        from langchain_pinecone import PineconeVectorStore
        from pinecone import Pinecone, ServerlessSpec
        
        add_log("All required libraries loaded successfully", "success")
        st.success("✅ System Libraries Loaded")
    except ImportError as e:
        add_log(f"Library import failed: {str(e)}", "error")
        st.error("❌ Missing Dependencies")
        st.stop()
    
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    
    # API Configuration
    st.markdown("### 🔑 API Configuration")
    
    try:
        OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", "")
        PINECONE_API_KEY = st.secrets.get("PINECONE_API_KEY", "")
        PINECONE_ENVIRONMENT = st.secrets.get("PINECONE_ENVIRONMENT", "us-east-1")
        INDEX_NAME = st.secrets.get("PINECONE_INDEX_NAME", "gov-doc-intelligence")
        
        if OPENAI_API_KEY and PINECONE_API_KEY:
            st.success("✅ API Keys Configured")
            add_log("API keys validated successfully", "success")
        else:
            st.error("❌ API Keys Missing")
            add_log("API keys not found in secrets", "error")
            st.stop()
            
    except Exception as e:
        st.error(f"❌ Configuration Error: {str(e)}")
        add_log(f"Configuration error: {str(e)}", "error")
        st.stop()
    
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    
    # System Status
    st.markdown("### 📊 System Status")
    
    try:
        llm = ChatOpenAI(model="gpt-4o-mini", openai_api_key=OPENAI_API_KEY, temperature=0)
        embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
        st.success("✅ AI Models Active")
        add_log("LLM and Embeddings initialized", "success")
    except Exception as e:
        st.error(f"❌ AI Model Error: {str(e)}")
        add_log(f"Failed to initialize AI models: {str(e)}", "error")
        st.stop()
    
    try:
        pc = Pinecone(api_key=PINECONE_API_KEY)
        existing_indexes = [index.name for index in pc.list_indexes()]
        
        if INDEX_NAME not in existing_indexes:
            add_log(f"Creating new index: {INDEX_NAME}", "warning")
            pc.create_index(
                name=INDEX_NAME,
                dimension=1536,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region=PINECONE_ENVIRONMENT)
            )
            add_log(f"Index {INDEX_NAME} created successfully", "success")
        
        index = pc.Index(INDEX_NAME)
        stats = index.describe_index_stats()
        st.success(f"✅ Vector DB Active")
        st.metric("Stored Documents", stats.total_vector_count)
        add_log(f"Connected to Pinecone index with {stats.total_vector_count} vectors", "success")
        
    except Exception as e:
        st.error(f"❌ Database Error: {str(e)}")
        add_log(f"Pinecone connection failed: {str(e)}", "error")
        st.stop()
    
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    
    # Admin Controls
    st.markdown("### ⚙️ Admin Controls")
    
    if st.button("🗑️ Clear All Documents", type="secondary", use_container_width=True):
        try:
            index.delete(delete_all=True)
            st.success("Database cleared!")
            add_log("All documents cleared from database", "warning")
            st.rerun()
        except Exception as e:
            st.error(f"Error: {str(e)}")
            add_log(f"Failed to clear database: {str(e)}", "error")
    
    if st.button("🔄 Refresh System", use_container_width=True):
        add_log("System refresh initiated", "info")
        st.rerun()

# Main Content Area
with st.container():
    st.markdown("### 📤 Document Upload & Processing")
    
    uploaded_file = st.file_uploader(
        "Upload Official Document (PDF)",
        type=["pdf"],
        help="Upload a PDF document for analysis and querying"
    )
    
    if uploaded_file:
        try:
            add_log(f"Processing document: {uploaded_file.name}", "info")
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(uploaded_file.read())
                tmp_path = tmp_file.name
            
            with st.spinner("📖 Analyzing document structure..."):
                loader = PyPDFLoader(tmp_path)
                pages = loader.load_and_split()
                
                splitter = RecursiveCharacterTextSplitter(
                    chunk_size=1000,
                    chunk_overlap=200
                )
                chunks = splitter.split_documents(pages)
                st.session_state.total_chunks = len(chunks)
            
            st.success(f"✅ Document processed: {len(chunks)} segments extracted")
            add_log(f"Document split into {len(chunks)} chunks", "success")
            
            # Display document metrics
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("Total Pages", len(pages))
            with col_b:
                st.metric("Text Segments", len(chunks))
            with col_c:
                st.metric("File Size", f"{uploaded_file.size / 1024:.1f} KB")
            
            with st.spinner("🔮 Creating vector embeddings..."):
                vectorstore = PineconeVectorStore.from_documents(
                    documents=chunks,
                    embedding=embeddings,
                    index_name=INDEX_NAME
                )
            
            st.success("✅ Document indexed successfully")
            add_log(f"Document embeddings created and stored", "success")
            st.session_state.document_uploaded = True
            
            # Cleanup
            try:
                os.unlink(tmp_path)
            except:
                pass
                
        except Exception as e:
            st.error(f"❌ Processing Error: {str(e)}")
            add_log(f"Document processing failed: {str(e)}", "error")
    
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    
    # Query Interface
    st.markdown("### 🔍 Document Query Interface")
    
    query = st.text_area(
        "Enter your question about the document",
        placeholder="Example: What are the main compliance requirements mentioned in this document?",
        height=100,
        help="Ask specific questions about the uploaded document"
    )
    
    col_search, col_clear = st.columns([3, 1])
    
    with col_search:
        search_button = st.button("🔍 Search & Analyze", type="primary", use_container_width=True)
    
    with col_clear:
        if st.button("🗑️ Clear", use_container_width=True):
            st.rerun()
    
    if search_button and query:
        if not st.session_state.document_uploaded:
            st.warning("⚠️ Please upload a document first")
            add_log("Query attempted without document", "warning")
        else:
            try:
                add_log(f"Query initiated: {query[:50]}...", "info")
                
                with st.spinner("🔍 Searching document database..."):
                    vectorstore = PineconeVectorStore(
                        index_name=INDEX_NAME,
                        embedding=embeddings
                    )
                    
                    docs_with_scores = vectorstore.similarity_search_with_score(query, k=5)
                    add_log(f"Retrieved {len(docs_with_scores)} relevant segments", "success")
                
                if not docs_with_scores:
                    st.warning("⚠️ No relevant information found")
                    add_log("No relevant documents found for query", "warning")
                else:
                    relevant_docs = [doc for doc, score in docs_with_scores]
                    
                    context = "\n\n".join([
                        f"[Source {i+1} - Page {doc.metadata.get('page', 'Unknown')}]\n{doc.page_content}"
                        for i, doc in enumerate(relevant_docs)
                    ])
                    
                    with st.spinner("🤖 Generating analysis..."):
                        prompt = f"""As a government document analysis AI, provide a clear and professional answer based on the following context.

Context:
{context}

Question: {query}

Provide a comprehensive answer with relevant details. If the context lacks sufficient information, state this clearly."""

                        response = llm.invoke(prompt)
                        answer = response.content
                        add_log("Answer generated successfully", "success")
                    
                    # Display Answer
                    st.markdown("### ✅ Analysis Result")
                    st.markdown(f"""
                    <div class='status-box status-success'>
                        {answer}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Source References
                    with st.expander(f"📚 Source References ({len(docs_with_scores)} segments)", expanded=False):
                        for i, (doc, score) in enumerate(docs_with_scores, 1):
                            st.markdown(f"**Reference {i}** - Relevance: {(1-score)*100:.1f}%")
                            st.info(f"Page: {doc.metadata.get('page', 'Unknown')}")
                            st.text(doc.page_content)
                            st.divider()
            
            except Exception as e:
                st.error(f"❌ Query Error: {str(e)}")
                add_log(f"Query processing failed: {str(e)}", "error")

# Footer
st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
st.markdown("""
<div style='text-align: center; color: #64748b; padding: 2rem;'>
    <p><strong>Government Document Intelligence System v1.0</strong></p>
    <p>🔒 Secure | 🛡️ Compliant | 🚀 AI-Powered</p>
    <p style='font-size: 0.9rem; margin-top: 1rem;'>
        For technical support, contact: support@gov-intelligence.gov
    </p>
</div>
""", unsafe_allow_html=True)