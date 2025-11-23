import streamlit as st
import tempfile
import os

# Show that app is loading
st.set_page_config(page_title="PDF RAG Assistant", page_icon="📄")

try:
    # --- LangChain imports ---
    from langchain_community.document_loaders import PyPDFLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings
    from langchain_pinecone import PineconeVectorStore
    from pinecone import Pinecone, ServerlessSpec
    
    imports_success = True
except ImportError as e:
    imports_success = False
    import_error = str(e)

# ------------------------------------------------------------
# 🖼️ Streamlit UI
# ------------------------------------------------------------

st.title("📄 PDF Vector DB RAG Assistant")
st.markdown("Upload a PDF, store embeddings in Pinecone, and ask questions.")

# Check imports
if not imports_success:
    st.error("❌ Missing required packages!")
    st.code(f"Error: {import_error}")
    st.markdown("""
    ### Install required packages:
    ```bash
    pip install streamlit langchain-community langchain-text-splitters langchain-openai langchain-pinecone pinecone-client pypdf
    ```
    """)
    st.stop()

st.success("✅ All packages loaded successfully")

# ------------------------------------------------------------
# 🔐 Load Streamlit Secrets
# ------------------------------------------------------------

st.subheader("🔐 Configuration Check")

secrets_status = {}

try:
    OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", "")
    secrets_status["OPENAI_API_KEY"] = "✅" if OPENAI_API_KEY else "❌ Missing"
except:
    OPENAI_API_KEY = ""
    secrets_status["OPENAI_API_KEY"] = "❌ Missing"

try:
    PINECONE_API_KEY = st.secrets.get("PINECONE_API_KEY", "")
    secrets_status["PINECONE_API_KEY"] = "✅" if PINECONE_API_KEY else "❌ Missing"
except:
    PINECONE_API_KEY = ""
    secrets_status["PINECONE_API_KEY"] = "❌ Missing"

try:
    PINECONE_ENVIRONMENT = st.secrets.get("PINECONE_ENVIRONMENT", "us-east-1")
    INDEX_NAME = st.secrets.get("PINECONE_INDEX_NAME", "pdf-rag-index")
    secrets_status["PINECONE_ENVIRONMENT"] = f"✅ {PINECONE_ENVIRONMENT}"
    secrets_status["PINECONE_INDEX_NAME"] = f"✅ {INDEX_NAME}"
except:
    PINECONE_ENVIRONMENT = "us-east-1"
    INDEX_NAME = "pdf-rag-index"
    secrets_status["PINECONE_ENVIRONMENT"] = f"⚠️ Using default: {PINECONE_ENVIRONMENT}"
    secrets_status["PINECONE_INDEX_NAME"] = f"⚠️ Using default: {INDEX_NAME}"

# Display secrets status
for key, status in secrets_status.items():
    st.text(f"{key}: {status}")

if not OPENAI_API_KEY or not PINECONE_API_KEY:
    st.error("❌ Required API keys are missing!")
    st.markdown("""
    ### Setup Instructions:
    
    Create a file `.streamlit/secrets.toml` with:
    ```toml
    OPENAI_API_KEY = "sk-your-key-here"
    PINECONE_API_KEY = "your-pinecone-key-here"
    PINECONE_ENVIRONMENT = "us-east-1"
    PINECONE_INDEX_NAME = "pdf-rag-index"
    ```
    
    **Get your API keys:**
    - OpenAI: https://platform.openai.com/api-keys
    - Pinecone: https://app.pinecone.io/ (free tier available)
    """)
    st.stop()

st.success("✅ All secrets configured")
st.divider()

# ------------------------------------------------------------
# 🧠 LLM & Embeddings Setup
# ------------------------------------------------------------

try:
    with st.spinner("Initializing LLM and Embeddings..."):
        llm = ChatOpenAI(
            model="gpt-4o-mini", 
            openai_api_key=OPENAI_API_KEY, 
            temperature=0
        )
        embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
    st.success("✅ LLM and Embeddings initialized")
except Exception as e:
    st.error(f"❌ Failed to initialize LLM/Embeddings: {e}")
    st.code(str(e))
    st.stop()

# ------------------------------------------------------------
# 🗄️ Initialize Pinecone
# ------------------------------------------------------------

try:
    with st.spinner("Connecting to Pinecone..."):
        pc = Pinecone(api_key=PINECONE_API_KEY)
        
        # Check if index exists
        existing_indexes = [index.name for index in pc.list_indexes()]
        
        if INDEX_NAME not in existing_indexes:
            st.warning(f"Index '{INDEX_NAME}' doesn't exist. Creating it...")
            pc.create_index(
                name=INDEX_NAME,
                dimension=1536,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region=PINECONE_ENVIRONMENT
                )
            )
            st.success(f"✅ Created new index: {INDEX_NAME}")
        else:
            # Get index stats
            index = pc.Index(INDEX_NAME)
            stats = index.describe_index_stats()
            st.success(f"✅ Connected to Pinecone index: {INDEX_NAME}")
            st.info(f"📊 Current vectors in database: {stats.total_vector_count}")
    
except Exception as e:
    st.error(f"❌ Failed to initialize Pinecone: {e}")
    st.code(str(e))
    st.markdown("""
    ### Common Pinecone Issues:
    1. **Invalid API Key**: Check your Pinecone API key
    2. **Wrong Region**: Verify PINECONE_ENVIRONMENT matches your Pinecone project
    3. **Free Tier Limits**: Free tier allows 1 index only
    
    Visit https://app.pinecone.io/ to check your settings
    """)
    st.stop()

st.divider()

# ------------------------------------------------------------
# 📤 UI Inputs
# ------------------------------------------------------------

st.subheader("📤 Upload & Query")

uploaded_file = st.file_uploader("Upload your PDF", type=["pdf"])
query = st.text_input("Ask a question about the document")

# Optional: Clear database button
col1, col2 = st.columns(2)
with col1:
    if st.button("🗑️ Clear Vector Database"):
        try:
            with st.spinner("Clearing database..."):
                index = pc.Index(INDEX_NAME)
                index.delete(delete_all=True)
            st.success("✅ Vector database cleared!")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Failed to clear database: {e}")

with col2:
    if st.button("📊 Check Database Stats"):
        try:
            index = pc.Index(INDEX_NAME)
            stats = index.describe_index_stats()
            st.json(stats)
        except Exception as e:
            st.error(f"Error: {e}")

# ------------------------------------------------------------
# 📚 Process PDF
# ------------------------------------------------------------

if uploaded_file:
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.read())
            tmp_path = tmp_file.name

        # Load + Split PDF
        with st.spinner("📖 Loading PDF..."):
            loader = PyPDFLoader(tmp_path)
            pages = loader.load_and_split()

            splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            chunks = splitter.split_documents(pages)

        st.success(f"✅ Loaded {len(chunks)} chunks from PDF")

        # ------------------------------------------------------------
        # 🔮 Create Embeddings and Store in Pinecone
        # ------------------------------------------------------------

        with st.spinner("🔮 Creating embeddings and storing in Pinecone..."):
            try:
                vectorstore = PineconeVectorStore.from_documents(
                    documents=chunks,
                    embedding=embeddings,
                    index_name=INDEX_NAME
                )
                
                st.success(f"✅ Successfully stored {len(chunks)} chunks in Pinecone!")
                
                # Show index stats
                index = pc.Index(INDEX_NAME)
                stats = index.describe_index_stats()
                st.info(f"📊 Total vectors in database: {stats.total_vector_count}")
                
            except Exception as e:
                st.error(f"❌ Failed to store embeddings: {e}")
                st.code(str(e))
                st.stop()

        # ------------------------------------------------------------
        # ❓ Answer Query (Without chains module)
        # ------------------------------------------------------------

        if query:
            try:
                with st.spinner("🔍 Searching vector database..."):
                    # Initialize vectorstore
                    vectorstore = PineconeVectorStore(
                        index_name=INDEX_NAME,
                        embedding=embeddings
                    )
                    
                    # Perform similarity search
                    docs_with_scores = vectorstore.similarity_search_with_score(query, k=5)
                    
                    if not docs_with_scores:
                        st.warning("No relevant documents found.")
                    else:
                        # Extract just the documents
                        relevant_docs = [doc for doc, score in docs_with_scores]
                        
                        # Build context from retrieved documents
                        context = "\n\n".join([
                            f"[Source {i+1} - Page {doc.metadata.get('page', 'Unknown')}]\n{doc.page_content}"
                            for i, doc in enumerate(relevant_docs)
                        ])
                        
                        # Generate answer using LLM
                        prompt = f"""Based on the following context from the document, please answer the question.

Context:
{context}

Question: {query}

Please provide a clear and concise answer based on the context above. If the context doesn't contain enough information, say so."""

                        response = llm.invoke(prompt)
                        answer = response.content
                        
                        # Display answer
                        st.subheader("✅ Answer")
                        st.write(answer)
                        
                        # Display source documents with scores
                        with st.expander(f"📚 Source Documents ({len(docs_with_scores)} chunks)"):
                            for i, (doc, score) in enumerate(docs_with_scores, 1):
                                st.markdown(f"**Chunk {i}** - Similarity Score: {score:.4f}")
                                st.markdown(f"Page: {doc.metadata.get('page', 'Unknown')}")
                                st.text(doc.page_content)
                                st.divider()
                
            except Exception as e:
                st.error(f"❌ Failed to run query: {e}")
                st.code(str(e))
                import traceback
                st.code(traceback.format_exc())
        
        # Cleanup
        try:
            os.unlink(tmp_path)
        except:
            pass
            
    except Exception as e:
        st.error(f"❌ Error processing PDF: {e}")
        import traceback
        st.code(traceback.format_exc())

else:
    st.info("👆 Upload a PDF to get started!")
    
st.divider()
st.markdown("""
### 📦 Installation:
```bash
pip install streamlit langchain-community langchain-text-splitters langchain-openai langchain-pinecone pinecone-client pypdf
```
""")