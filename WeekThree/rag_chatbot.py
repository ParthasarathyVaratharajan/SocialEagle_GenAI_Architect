import numpy as np
from typing import List
import streamlit as st
import PyPDF2
from openai import OpenAI


def extract_text_from_pdf(file) -> str:
    """Extract text from PDF file."""
    try:
        reader = PyPDF2.PdfReader(file)
        texts = []
        for p, page in enumerate(reader.pages):
            try:
                txt = page.extract_text() or ""
            except Exception:
                txt = ""
            if txt:
                texts.append(f"[page_{p+1}]\n" + txt)
        return "\n\n".join(texts)
    except Exception as e:
        raise Exception(f"Error extracting PDF: {e}")


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """Split text into overlapping chunks."""
    if not text:
        return []
    chunks = []
    start = 0
    L = len(text)
    while start < L:
        end = min(start + chunk_size, L)
        chunk = text[start:end]
        chunks.append(chunk)
        if end == L:
            break
        start = end - overlap
    return chunks


def compute_embeddings(texts: List[str], api_key: str, model: str = "text-embedding-3-small") -> List[List[float]]:
    """Compute embeddings using OpenAI API with user-provided key."""
    if not texts:
        return []
    try:
        client = OpenAI(api_key=api_key)
        resp = client.embeddings.create(input=texts, model=model)
        return [r.embedding for r in resp.data]
    except Exception as e:
        raise Exception(f"Error computing embeddings: {e}")


def call_chat_model(system_prompt: str, user_prompt: str, api_key: str, 
                   temperature: float = 0.0, model: str = "gpt-3.5-turbo") -> str:
    """Call OpenAI ChatCompletion with user-provided API key."""
    try:
        client = OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=800,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        raise Exception(f"LLM call failed: {e}")


def make_system_prompt() -> str:
    """Create strict system prompt that enforces context-only answers."""
    return (
        "You are a helpful assistant that MUST answer using ONLY the provided CONTEXT. "
        "Do NOT use external knowledge or make assumptions. "
        "If the answer is not present in the context, reply exactly: \"I don't know based on the provided document.\" "
        "When you do answer, be concise and cite the chunk index in square brackets (example: [0,2])."
    )


def build_context_for_prompt(retrieved: List[dict]) -> str:
    """Build context string from retrieved chunks."""
    parts = []
    for r in retrieved:
        header = f"--- CHUNK {r.get('index', 0)} (score: {r.get('score',0):.4f}) ---"
        parts.append(header + "\n" + r.get("text", ""))
    return "\n\n".join(parts)


def main():
    st.set_page_config(page_title="PDF-only RAG Chatbot", layout="wide")
    st.title("🤖 PDF-only RAG Chatbot")
    st.markdown("Ask questions about your uploaded PDF. Answers are based **exclusively** on the document.")

    # Sidebar Configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # API Key Input
        api_key = st.text_input("Enter OpenAI API Key", type="password", key="api_key")
        if api_key:
            st.success("✓ API Key loaded")
        else:
            st.warning("⚠️ API Key required to proceed")
        
        # File Upload
        uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"])
        
        # Retrieval Settings
        st.markdown("---")
        st.subheader("Retrieval Settings")
        top_k = st.slider("Number of chunks to retrieve", 1, 10, 4)
        chunk_size = st.slider("Chunk size (characters)", 200, 2000, 1000, step=100)
        overlap = st.slider("Chunk overlap (characters)", 0, 500, 200, step=50)
        
        st.markdown("---")
        if st.button("🗑️ Clear Chat History"):
            st.session_state.history = []
            st.rerun()

    # Initialize session state
    if "history" not in st.session_state:
        st.session_state.history = []

    # Main content
    if not api_key:
        st.error("Please provide your OpenAI API Key in the sidebar to continue.")
        st.stop()

    if uploaded_file is None:
        st.info("👈 Please upload a PDF file in the sidebar to get started.")
        st.stop()

    # Process PDF
    with st.spinner("📄 Extracting text from PDF..."):
        try:
            pdf_text = extract_text_from_pdf(uploaded_file)
            if not pdf_text.strip():
                st.error("No extractable text found in PDF.")
                st.stop()
        except Exception as e:
            st.error(f"Failed to extract PDF: {e}")
            st.stop()

    # Chunk and embed
    chunk_texts = chunk_text(pdf_text, chunk_size=chunk_size, overlap=overlap)
    st.success(f"✓ Document processed into {len(chunk_texts)} chunks")

    # Compute embeddings once per file
    cache_key = f"_embeddings_{len(chunk_texts)}_{chunk_size}_{overlap}"
    if cache_key not in st.session_state:
        with st.spinner("🔢 Computing embeddings for chunks..."):
            try:
                chunk_embeddings = compute_embeddings(chunk_texts, api_key)
                st.session_state.chunk_embeddings = chunk_embeddings
                st.session_state.chunk_texts = chunk_texts
                st.session_state[cache_key] = True
            except Exception as e:
                st.error(f"Failed to compute embeddings: {e}")
                st.stop()
    else:
        chunk_embeddings = st.session_state.chunk_embeddings

    # Chat Interface
    st.markdown("---")
    st.subheader("💬 Ask a Question")
    
    col1, col2 = st.columns([4, 1])
    with col1:
        query = st.text_input("Your question about the PDF:", placeholder="What is the main topic of this document?")
    with col2:
        ask_btn = st.button("Ask", use_container_width=True)

    if ask_btn and query.strip():
        # Retrieve relevant chunks
        with st.spinner("🔍 Retrieving relevant chunks..."):
            try:
                query_embeddings = compute_embeddings([query], api_key)
                query_emb = np.array(query_embeddings[0], dtype=np.float32)
                chunk_matrix = np.array(chunk_embeddings, dtype=np.float32)
                
                # Cosine similarity
                norms = np.linalg.norm(chunk_matrix, axis=1, keepdims=True)
                norm_q = np.linalg.norm(query_emb)
                if norm_q == 0:
                    scores = np.zeros(len(chunk_embeddings))
                else:
                    scores = (chunk_matrix @ query_emb) / (norms.flatten() * norm_q + 1e-12)
                
                top_indices = np.argsort(scores)[::-1][:top_k]
                retrieved = [
                    {
                        "score": float(scores[i]),
                        "text": chunk_texts[i],
                        "index": int(i)
                    }
                    for i in top_indices
                ]
            except Exception as e:
                st.error(f"Retrieval failed: {e}")
                retrieved = []

        if not retrieved:
            st.warning("No relevant chunks found.")
        else:
            # Build context and generate answer
            context = build_context_for_prompt(retrieved)
            system_prompt = make_system_prompt()
            user_prompt = f"QUESTION:\n{query}\n\nCONTEXT:\n{context}\n\nAnswer based solely on the context provided. If the answer is not in the context, respond: I don't know based on the provided document."

            with st.spinner("🤔 Generating answer..."):
                try:
                    answer = call_chat_model(system_prompt, user_prompt, api_key, temperature=0.0)
                except Exception as e:
                    answer = f"Error: {e}"

            # Store in history
            st.session_state.history.append({
                "query": query,
                "answer": answer,
                "retrieved": retrieved
            })

    # Display chat history (most recent first)
    st.markdown("---")
    st.subheader("📋 Conversation History")
    
    if not st.session_state.history:
        st.info("No questions asked yet.")
    else:
        for i, item in enumerate(reversed(st.session_state.history)):
            with st.container():
                st.markdown(f"**Q:** {item['query']}")
                st.markdown(f"**A:** {item['answer']}")
                
                # Show retrieved chunks in expander
                with st.expander(f"View {len(item.get('retrieved', []))} retrieved chunks"):
                    for r in item.get("retrieved", []):
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(f"**Chunk {r['index']}**")
                        with col2:
                            st.write(f"Score: {r['score']:.3f}")
                        st.text(r['text'][:500] + "..." if len(r['text']) > 500 else r['text'])
                        st.divider()


if __name__ == "__main__":
    main()
