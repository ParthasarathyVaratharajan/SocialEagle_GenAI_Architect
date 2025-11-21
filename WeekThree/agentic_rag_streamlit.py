import streamlit as st
import re
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WikipediaLoader
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

# Page config
st.set_page_config(page_title="Agentic RAG Chatbot", layout="wide", initial_sidebar_state="expanded")
st.title("🤖 Agentic RAG Chatbot with Agent Reasoning")
st.markdown("""
Ask questions and watch the **AI Agent** think step-by-step:
- **Thought**: Agent's reasoning about what to do
- **Action**: Tool used (retrieve documents, generate answer, etc.)
- **Observation**: Results from the action
- **Final Answer**: Agent's final response based on observations
""")

# Sidebar Configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("OpenAI API Key", type="password", help="Required for agent reasoning")
    
    topic = st.selectbox(
        "Knowledge Base Topic",
        ["Artificial Intelligence", "Machine Learning", "Deep Learning", "Python", "Data Science"],
        help="Select topic to load Wikipedia documents"
    )
    
    agent_model = st.selectbox(
        "Agent Model",
        ["gpt-3.5-turbo", "gpt-4"],
        help="Model for agent reasoning and decision-making"
    )
    
    max_iterations = st.slider("Max Agent Iterations", 1, 10, 5, help="Max reasoning steps")
    
    enable_agent_trace = st.checkbox("Show Agent Trace", value=True, help="Display reasoning steps")

# Initialize session state
if "vectordb" not in st.session_state:
    st.session_state.vectordb = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "initialized" not in st.session_state:
    st.session_state.initialized = False
if "agent_trace" not in st.session_state:
    st.session_state.agent_trace = []

# Define Agent Tools
def retrieve_documents(query: str) -> str:
    """Retrieve relevant documents from the knowledge base."""
    if not st.session_state.vectordb:
        return "Knowledge base not initialized."
    try:
        retriever = st.session_state.vectordb.as_retriever(search_kwargs={"k": 3})
        docs = retriever.invoke(query)
        context = "\n\n".join([f"[Doc {i+1}] {d.page_content[:500]}" for i, d in enumerate(docs)])
        return context if context else "No relevant documents found."
    except Exception as e:
        return f"Error retrieving documents: {str(e)}"


def generate_answer(context: str, question: str, api_key: str) -> str:
    """Generate an answer based on context and question."""
    try:
        llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.0, api_key=api_key)
        prompt = ChatPromptTemplate.from_template(
            """Based on the provided context, answer the question concisely.
If the context doesn't contain the answer, state that clearly.

Context: {context}
Question: {question}
Answer:"""
        )
        chain = prompt | llm
        result = chain.invoke({"context": context[:2000], "question": question})
        return result.content
    except Exception as e:
        return f"Error generating answer: {str(e)}"


def check_answer_quality(answer: str) -> str:
    """Check if the answer is complete and addresses the question."""
    if not answer or "I don't" in answer or "unclear" in answer.lower():
        return "INCOMPLETE: Answer may need more research or clarification."
    return "COMPLETE: Answer appears sufficient."


# Main Layout: Two columns
col1, col2 = st.columns([2, 1], gap="medium")

with col1:
    st.subheader("💬 Chat with Agent")
    
    # Display chat history
    chat_container = st.container(height=400, border=True)
    with chat_container:
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

with col2:
    st.subheader("📚 Knowledge Base Status")
    
    # Initialize Knowledge Base
    if not st.session_state.initialized and api_key:
        with st.spinner(f"Loading {topic} knowledge base..."):
            try:
                # Sanitize topic name
                safe_topic = re.sub(r'[^a-zA-Z0-9._-]+', '_', topic.lower()).strip('_')
                
                # Load Wikipedia documents
                loader = WikipediaLoader(topic, lang="en", load_max_docs=1)
                docs = loader.load()
                
                if docs:
                    text = docs[0].page_content
                    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
                    chunks = splitter.split_text(text)
                    
                    # Create embeddings and vector store
                    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
                    db_path = f"./chroma_agentic_rag_{safe_topic}"
                    st.session_state.vectordb = Chroma.from_texts(
                        chunks,
                        embedding=embeddings,
                        persist_directory=db_path,
                        collection_name=f"agentic_rag_{safe_topic}"
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
        st.warning("⚠️ Enter OpenAI API Key")

# Agent Thinking Process Display
if enable_agent_trace and st.session_state.agent_trace:
    st.divider()
    st.subheader("🧠 Agent Thinking Process")
    for step in st.session_state.agent_trace:
        with st.expander(f"{step['type'].upper()}: {step['content'][:60]}..."):
            st.write(step['content'])

# User Input and Agent Execution
st.divider()
user_input = st.chat_input(
    "Ask the agent a question...",
    disabled=not (st.session_state.initialized and api_key)
)

if user_input:
    # Add user message to history
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    st.session_state.agent_trace = []  # Reset trace for new query
    
    # Agent Loop: Think → Act → Observe → Conclude
    with st.spinner("🤔 Agent thinking..."):
        try:
            step = 0
            final_answer = ""
            context = ""
            
            # Step 1: Retrieve
            st.session_state.agent_trace.append({
                "type": "thought",
                "content": f"I need to find information about: {user_input}"
            })
            
            context = retrieve_documents(user_input)
            st.session_state.agent_trace.append({
                "type": "action",
                "content": "retrieve_documents"
            })
            st.session_state.agent_trace.append({
                "type": "observation",
                "content": context
            })
            
            # Step 2: Generate Answer
            st.session_state.agent_trace.append({
                "type": "thought",
                "content": "Now I'll generate a comprehensive answer based on the retrieved documents."
            })
            
            final_answer = generate_answer(context, user_input, api_key)
            st.session_state.agent_trace.append({
                "type": "action",
                "content": "generate_answer"
            })
            st.session_state.agent_trace.append({
                "type": "observation",
                "content": final_answer
            })
            
            # Step 3: Check Quality
            st.session_state.agent_trace.append({
                "type": "thought",
                "content": "Let me verify if my answer is complete and addresses the question."
            })
            
            quality_check = check_answer_quality(final_answer)
            st.session_state.agent_trace.append({
                "type": "action",
                "content": "check_answer_quality"
            })
            st.session_state.agent_trace.append({
                "type": "observation",
                "content": quality_check
            })
            
            # Step 4: Final Reasoning
            if "INCOMPLETE" in quality_check:
                st.session_state.agent_trace.append({
                    "type": "thought",
                    "content": "The answer may be incomplete. I should provide a more detailed response or acknowledge limitations."
                })
                final_answer = f"{final_answer}\n\n**Note:** {quality_check}"
            else:
                st.session_state.agent_trace.append({
                    "type": "thought",
                    "content": "I have sufficient information to provide a complete answer."
                })
            
            # Add assistant message to history
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": final_answer
            })
            
            # Display response
            st.chat_message("assistant").write(final_answer)
            
            # Show agent trace if enabled
            if enable_agent_trace:
                st.divider()
                st.subheader("🧠 Agent Reasoning Steps")
                for i, step in enumerate(st.session_state.agent_trace, 1):
                    with st.expander(f"Step {i}: {step['type'].upper()}"):
                        st.write(step['content'])
            
        except Exception as e:
            st.error(f"Agent Error: {str(e)}")
            st.session_state.agent_trace.append({
                "type": "error",
                "content": str(e)
            })

# Footer
st.divider()
st.caption("🔍 Agentic RAG using LangChain, Agent Framework, Chroma, HuggingFace, and OpenAI | Data from Wikipedia")
