import streamlit as st
import tempfile
import os

# --- LangChain imports ---
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI
from langchain_community.graphs import Neo4jGraph

# ------------------------------------------------------------
# 🖼️ Streamlit UI
# ------------------------------------------------------------

st.title("📄 PDF Knowledge Graph RAG Assistant")
st.markdown("Upload a PDF, build a knowledge graph, and ask grounded questions.")

# ------------------------------------------------------------
# 🔐 Load Streamlit Secrets
# ------------------------------------------------------------

try:
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
    NEO4J_URI = st.secrets["NEO4J_URI"]
    NEO4J_USER = st.secrets["NEO4J_USER"]
    NEO4J_PASSWORD = st.secrets["NEO4J_PASSWORD"]
except Exception as e:
    st.error("❌ Secrets not configured properly. Check `.streamlit/secrets.toml`.")
    st.stop()

# ------------------------------------------------------------
# 🧠 LLM Setup
# ------------------------------------------------------------

try:
    llm = ChatOpenAI(model="gpt-4o-mini", openai_api_key=OPENAI_API_KEY, temperature=0)
except Exception as e:
    st.error(f"❌ Failed to initialize LLM: {e}")
    st.stop()

# ------------------------------------------------------------
# 📤 UI Inputs
# ------------------------------------------------------------

uploaded_file = st.file_uploader("Upload your PDF", type=["pdf"])
query = st.text_input("Ask a question about the document")

# ------------------------------------------------------------
# 📚 Process PDF
# ------------------------------------------------------------

if uploaded_file:
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.read())
            tmp_path = tmp_file.name

        # Load + Split PDF
        loader = PyPDFLoader(tmp_path)
        pages = loader.load_and_split()

        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        chunks = splitter.split_documents(pages)

        st.success(f"✅ Loaded {len(chunks)} chunks from PDF")

        # ------------------------------------------------------------
        # 🕸️ Connect to Neo4j
        # ------------------------------------------------------------

        try:
            graph = Neo4jGraph(
                url=NEO4J_URI,
                username=NEO4J_USER,
                password=NEO4J_PASSWORD
            )
            st.success("✅ Connected to Neo4j")
        except Exception as e:
            st.error(f"❌ Failed to connect to Neo4j: {e}")
            st.stop()

        # ------------------------------------------------------------
        # 🧩 Insert chunks into Graph
        # ------------------------------------------------------------

        try:
            # Clear existing data for fresh upload
            graph.query("MATCH (n:Chunk) DELETE n")
            
            for i, doc in enumerate(chunks):
                graph.query(
                    """
                    CREATE (c:Chunk {
                        id: $id,
                        content: $content, 
                        page: $page,
                        chunk_index: $chunk_index
                    })
                    """,
                    {
                        "id": f"chunk_{i}",
                        "content": doc.page_content,
                        "page": str(doc.metadata.get("page", "Unknown")),
                        "chunk_index": i
                    }
                )
            st.success(f"✅ Inserted {len(chunks)} chunks into Neo4j")
        except Exception as e:
            st.error(f"❌ Failed to insert chunks into Neo4j: {e}")
            st.stop()

        # ------------------------------------------------------------
        # ❓ Answer Query
        # ------------------------------------------------------------

        if query:
            try:
                with st.spinner("🔍 Searching knowledge graph..."):
                    # Step 1: Retrieve relevant chunks using Cypher
                    cypher_query = """
                    MATCH (c:Chunk)
                    WHERE toLower(c.content) CONTAINS toLower($query_text)
                    RETURN c.content AS content, c.page AS page, c.chunk_index AS chunk_index
                    ORDER BY c.chunk_index
                    LIMIT 5
                    """
                    
                    #st.code(cypher_query, language="cypher")
                    
                    results = graph.query(cypher_query, {"query_text": query})
                    
                    if results:
                        st.success(f"✅ Found {len(results)} relevant chunks")
                        
                        # Step 2: Build context from retrieved chunks
                        context_parts = []
                        for i, result in enumerate(results, 1):
                            context_parts.append(
                                f"[Chunk {i} - Page {result['page']}]\n{result['content']}"
                            )
                        
                        context = "\n\n".join(context_parts)
                        
                        # Show retrieved context
                        with st.expander("📚 Retrieved Context"):
                            st.text(context)
                        
                        # Step 3: Generate answer using LLM with context
                        prompt = f"""Based on the following information from the document, please answer the question.

Context:
{context}

Question: {query}

Please provide a clear and concise answer based only on the information provided in the context above. If the context doesn't contain enough information to answer the question, please say so."""

                        answer = llm.predict(prompt)
                        
                        st.subheader("✅ Answer")
                        st.write(answer)
                        
                    else:
                        st.warning("⚠️ No matching content found in the knowledge graph.")
                        st.info("💡 Try rephrasing your question or using different keywords.")
                        
                        # Fallback: Show what's available
                        sample_query = """
                        MATCH (c:Chunk)
                        RETURN c.content AS content
                        LIMIT 3
                        """
                        sample_results = graph.query(sample_query)
                        
                        if sample_results:
                            with st.expander("📄 Sample content from document"):
                                for r in sample_results:
                                    st.text(r['content'][:200] + "...")
                
            except Exception as e:
                st.error(f"❌ Failed to run query: {e}")
                st.write("**Error details:**", str(e))
        
        # Cleanup temp file
        try:
            os.unlink(tmp_path)
        except:
            pass
            
    except Exception as e:
        st.error(f"❌ Error processing PDF: {e}")
        import traceback
        st.code(traceback.format_exc())

else:
    if query:
        st.warning("⚠️ Please upload a PDF before asking questions.")