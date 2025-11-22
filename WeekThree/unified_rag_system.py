import streamlit as st
import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"
from dotenv import load_dotenv
from typing import Dict
from dataclasses import dataclass
from enum import Enum
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import PyPDFLoader, TextLoader
import requests
import tempfile

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Unified RAG System",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 2rem 0 1rem 0;
        margin-bottom: 0.5rem;
    }
    
    .sub-header {
        text-align: center;
        color: #666;
        font-size: 1.2rem;
        margin-bottom: 2rem;
        font-weight: 500;
    }
    
    .rag-card {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
        border-left: 4px solid #667eea;
        padding: 1.5rem;
        border-radius: 1rem;
        margin: 1rem 0;
        transition: all 0.3s;
    }
    
    .rag-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.2);
    }
    
    .metric-box {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 1rem;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    
    .info-badge {
        display: inline-block;
        padding: 0.4rem 1rem;
        border-radius: 2rem;
        font-size: 0.85rem;
        font-weight: 600;
        margin: 0.25rem;
    }
    
    .badge-corrective {
        background: linear-gradient(90deg, #f093fb 0%, #f5576c 100%);
        color: white;
    }
    
    .badge-fallback {
        background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%);
        color: white;
    }
    
    .badge-websearch {
        background: linear-gradient(90deg, #43e97b 0%, #38f9d7 100%);
        color: white;
    }
    
    .badge-adaptive {
        background: linear-gradient(90deg, #fa709a 0%, #fee140 100%);
        color: white;
    }
    
    .badge-unified {
        background: linear-gradient(90deg, #30cfd0 0%, #330867 100%);
        color: white;
    }
    
    .chat-message {
        padding: 1.5rem;
        border-radius: 1rem;
        margin-bottom: 1.5rem;
    }
    
    .user-message {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
        border-left: 5px solid #667eea;
    }
    
    .bot-message {
        background: linear-gradient(135deg, rgba(17, 153, 142, 0.1) 0%, rgba(56, 239, 125, 0.1) 100%);
        border-left: 5px solid #11998e;
    }
    
    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 0.75rem;
        font-weight: bold;
        font-size: 1rem;
        transition: all 0.3s;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    
    .stButton>button:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }
    
    .parameter-section {
        background: rgba(255, 255, 255, 0.05);
        padding: 1rem;
        border-radius: 0.75rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Quality Level Enum
class QualityLevel(Enum):
    EXCELLENT = "EXCELLENT"
    GOOD = "GOOD"
    AVERAGE = "AVERAGE"
    POOR = "POOR"

@dataclass
class ContextEvaluation:
    relevance_score: float
    accuracy_score: float
    completeness_score: float
    specificity_score: float
    overall_quality: QualityLevel
    reasoning: str

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'documents' not in st.session_state:
    st.session_state.documents = []
if 'vectorstore' not in st.session_state:
    st.session_state.vectorstore = None
if 'stats' not in st.session_state:
    st.session_state.stats = {
        'corrective': 0,
        'fallback': 0,
        'websearch': 0,
        'adaptive': 0,
        'unified': 0
    }
if 'uploaded_files_info' not in st.session_state:
    st.session_state.uploaded_files_info = []
if 'chunk_count' not in st.session_state:
    st.session_state.chunk_count = 0
if 'data_source' not in st.session_state:
    st.session_state.data_source = None

# RAG System Classes
class CorrectiveRAG:
    def __init__(self, model_name: str = "gpt-4o-mini", temperature: float = 0.0):
        self.model = ChatOpenAI(model=model_name, temperature=temperature)
    
    def evaluate_context(self, query: str, context: str) -> ContextEvaluation:
        prompt = ChatPromptTemplate.from_template("""
        You are a context evaluator. Evaluate the quality of the given context for the query.
        
        Context: {context}
        Query: {query}
        
        Evaluate on these criteria (score 0-1):
        1. Relevance: How well does it address the query?
        2. Completeness: Does it provide sufficient information?
        3. Accuracy: Is the information factually correct?
        4. Specificity: Is it specific enough for the query?
        
        Respond with scores in this format:
        RELEVANCE: <score>
        COMPLETENESS: <score>
        ACCURACY: <score>
        SPECIFICITY: <score>
        OVERALL: <EXCELLENT/GOOD/AVERAGE/POOR>
        REASONING: <brief explanation>
        """)
        
        response = self.model.invoke(prompt.format(context=context, query=query))
        lines = response.content.strip().split('\n')
        scores = {}
        reasoning = ""
        overall = QualityLevel.AVERAGE
        
        for line in lines:
            if line.startswith("RELEVANCE:"):
                scores['relevance'] = float(line.split(':')[1].strip())
            elif line.startswith("COMPLETENESS:"):
                scores['completeness'] = float(line.split(':')[1].strip())
            elif line.startswith("ACCURACY:"):
                scores['accuracy'] = float(line.split(':')[1].strip())
            elif line.startswith("SPECIFICITY:"):
                scores['specificity'] = float(line.split(':')[1].strip())
            elif line.startswith("OVERALL:"):
                overall_str = line.split(':')[1].strip()
                try:
                    overall = QualityLevel[overall_str]
                except:
                    overall = QualityLevel.AVERAGE
            elif line.startswith("REASONING:"):
                reasoning = line.split(':', 1)[1].strip()
        
        return ContextEvaluation(
            relevance_score=scores.get('relevance', 0.0),
            completeness_score=scores.get('completeness', 0.0),
            accuracy_score=scores.get('accuracy', 0.0),
            specificity_score=scores.get('specificity', 0.0),
            overall_quality=overall,
            reasoning=reasoning
        )
    
    def refine_query(self, original_query: str, evaluation: ContextEvaluation) -> str:
        refine_prompt = ChatPromptTemplate.from_template("""
The original query did not retrieve good context.

Original Query: {query}
Problem: {reasoning}

Create a refined search query that will retrieve better context.
Focus on: keywords, specific terms, and related concepts.

Refined Query:""")
        
        response = self.model.invoke(
            refine_prompt.format(
                query=original_query,
                reasoning=evaluation.reasoning
            )
        )
        
        return response.content.strip()
    
    def process_query(self, query: str, vectorstore, max_attempts: int = 3) -> Dict:
        """Process query with correction mechanism"""
        attempt = 1
        correction_needed = False
        
        while attempt <= max_attempts:
            # Retrieve context
            if attempt == 1:
                search_query = query
            else:
                search_query = self.refine_query(query, evaluation)
                correction_needed = True
            
            docs = vectorstore.similarity_search(search_query, k=5)
            context = "\n\n".join([doc.page_content for doc in docs])
            
            # Evaluate context
            evaluation = self.evaluate_context(query, context)
            
            # Check if quality is acceptable
            if evaluation.overall_quality in [QualityLevel.GOOD, QualityLevel.EXCELLENT]:
                break
            
            attempt += 1
        
        # Generate final answer
        answer_prompt = ChatPromptTemplate.from_template("""
Based on the following context, answer the query.

Query: {query}
Context: {context}

Answer:""")
        
        response = self.model.invoke(
            answer_prompt.format(query=query, context=context)
        )
        
        return {
            "answer": response.content,
            "quality": evaluation.overall_quality.value,
            "correction_applied": correction_needed,
            "attempts": attempt
        }

class FallbackRAG:
    def __init__(self, model_name: str = "gpt-4o-mini"):
        self.model = ChatOpenAI(model=model_name, temperature=0.7)
        self.fallback_levels = [
            {"k": 5, "threshold": 0.7},
            {"k": 10, "threshold": 0.6},
            {"k": 15, "threshold": 0.5},
            {"k": 20, "threshold": 0.4},
            {"k": 25, "threshold": 0.3}
        ]
    
    def process_query(self, query: str, vectorstore) -> Dict:
        """Process with 5 fallback levels"""
        for level, config in enumerate(self.fallback_levels, 1):
            docs = vectorstore.similarity_search(query, k=config['k'])
            
            if docs:
                context = "\n\n".join([doc.page_content for doc in docs])
                
                answer_prompt = ChatPromptTemplate.from_template("""
Based on the following context, answer the query.

Query: {query}
Context: {context}

Answer:""")
                
                response = self.model.invoke(
                    answer_prompt.format(query=query, context=context)
                )
                
                if len(response.content.strip()) > 50:
                    return {
                        "answer": response.content,
                        "level": level,
                        "docs_retrieved": len(docs)
                    }
        
        return {
            "answer": "Could not find sufficient information after all fallback attempts.",
            "level": 5,
            "docs_retrieved": 0
        }

class WebSearchRAG:
    def __init__(self, model_name: str = "gpt-4o-mini"):
        self.model = ChatOpenAI(model=model_name, temperature=0.7)
    
    def search_web(self, query: str) -> str:
        """Search web using SERPAPI"""
        try:
            serpapi_key = os.getenv("SERPAPI_API_KEY")
            if not serpapi_key:
                return None
            
            params = {
                "engine": "google",
                "q": query,
                "api_key": serpapi_key
            }
            
            response = requests.get("https://www.searchapi.io/api/v1/search", params=params)
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            
            search_results = ""
            if "organic_results" in data and len(data["organic_results"]) > 0:
                for i, result in enumerate(data["organic_results"][:5], 1):
                    title = result.get("title", "")
                    snippet = result.get("snippet", "")
                    search_results += f"{i}. {title}\n{snippet}\n\n"
            
            return search_results
        except:
            return None
    
    def process_query(self, query: str, vectorstore=None, use_internal: bool = True) -> Dict:
        """Combine internal + web search intelligently"""
        internal_answer = None
        web_answer = None
        
        # Try internal search first if enabled
        if use_internal and vectorstore:
            docs = vectorstore.similarity_search(query, k=5)
            if docs:
                context = "\n\n".join([doc.page_content for doc in docs])
                
                prompt = ChatPromptTemplate.from_template("""
Based on the following context, answer the query.
If the context is not sufficient, respond with "INSUFFICIENT".

Query: {query}
Context: {context}

Answer:""")
                
                response = self.model.invoke(prompt.format(query=query, context=context))
                if "INSUFFICIENT" not in response.content:
                    internal_answer = response.content
        
        # Try web search
        web_results = self.search_web(query)
        if web_results:
            prompt = ChatPromptTemplate.from_template("""
Based on the following web search results, provide a comprehensive answer.

Query: {query}
Web Results: {results}

Answer:""")
            
            response = self.model.invoke(prompt.format(query=query, results=web_results))
            web_answer = response.content
        
        # Combine results
        if internal_answer and web_answer:
            combine_prompt = ChatPromptTemplate.from_template("""
Combine these two answers into a comprehensive response:

Internal Knowledge: {internal}
Web Search: {web}

Combined Answer:""")
            
            response = self.model.invoke(
                combine_prompt.format(internal=internal_answer, web=web_answer)
            )
            return {
                "answer": response.content,
                "source": "combined",
                "used_internal": True,
                "used_web": True
            }
        elif internal_answer:
            return {
                "answer": internal_answer,
                "source": "internal",
                "used_internal": True,
                "used_web": False
            }
        elif web_answer:
            return {
                "answer": web_answer,
                "source": "web",
                "used_internal": False,
                "used_web": True
            }
        else:
            return {
                "answer": "Could not find information from internal or web sources.",
                "source": "none",
                "used_internal": False,
                "used_web": False
            }

class AdaptiveRAG:
    def __init__(self, model_name: str = "gpt-4o-mini"):
        self.model = ChatOpenAI(model=model_name, temperature=0.7)
    
    def analyze_query(self, query: str) -> Dict:
        """Analyze query complexity and user level"""
        prompt = ChatPromptTemplate.from_template("""
Analyze this query and determine:
1. Complexity: SIMPLE, MODERATE, COMPLEX
2. User Level: BEGINNER, INTERMEDIATE, EXPERT
3. Topic: Brief topic description

Query: {query}

Respond in format:
COMPLEXITY: <level>
USER_LEVEL: <level>
TOPIC: <topic>
""")
        
        response = self.model.invoke(prompt.format(query=query))
        lines = response.content.strip().split('\n')
        
        analysis = {
            "complexity": "MODERATE",
            "user_level": "INTERMEDIATE",
            "topic": "General"
        }
        
        for line in lines:
            if line.startswith("COMPLEXITY:"):
                analysis["complexity"] = line.split(':')[1].strip()
            elif line.startswith("USER_LEVEL:"):
                analysis["user_level"] = line.split(':')[1].strip()
            elif line.startswith("TOPIC:"):
                analysis["topic"] = line.split(':', 1)[1].strip()
        
        return analysis
    
    def process_query(self, query: str, vectorstore) -> Dict:
        """Adjust to query complexity and user level"""
        analysis = self.analyze_query(query)
        
        # Adjust k based on complexity
        k_map = {"SIMPLE": 3, "MODERATE": 5, "COMPLEX": 10}
        k = k_map.get(analysis["complexity"], 5)
        
        docs = vectorstore.similarity_search(query, k=k)
        context = "\n\n".join([doc.page_content for doc in docs])
        
        # Adjust response style based on user level
        style_map = {
            "BEGINNER": "Explain in simple terms with examples.",
            "INTERMEDIATE": "Provide a balanced explanation with some technical details.",
            "EXPERT": "Provide a detailed technical explanation."
        }
        style = style_map.get(analysis["user_level"], style_map["INTERMEDIATE"])
        
        prompt = ChatPromptTemplate.from_template("""
Based on the following context, answer the query.
{style}

Query: {query}
Context: {context}

Answer:""")
        
        response = self.model.invoke(
            prompt.format(query=query, context=context, style=style)
        )
        
        return {
            "answer": response.content,
            "complexity": analysis["complexity"],
            "user_level": analysis["user_level"],
            "topic": analysis["topic"],
            "docs_used": k
        }

class UnifiedRAGSystem:
    def __init__(self, model_name: str = "gpt-4o-mini"):
        self.corrective = CorrectiveRAG(model_name)
        self.fallback = FallbackRAG(model_name)
        self.websearch = WebSearchRAG(model_name)
        self.adaptive = AdaptiveRAG(model_name)
        self.model = ChatOpenAI(model=model_name, temperature=0.7)
    
    def select_best_method(self, query: str) -> str:
        """Auto-select best RAG method for query"""
        prompt = ChatPromptTemplate.from_template("""
Analyze this query and select the best RAG method:

1. CORRECTIVE - For queries needing quality evaluation and refinement
2. FALLBACK - For queries that might need multiple retrieval attempts
3. WEBSEARCH - For queries needing current/external information
4. ADAPTIVE - For queries with varying complexity levels

Query: {query}

Respond with just the method name: CORRECTIVE, FALLBACK, WEBSEARCH, or ADAPTIVE
""")
        
        response = self.model.invoke(prompt.format(query=query))
        method = response.content.strip().upper()
        
        if method not in ["CORRECTIVE", "FALLBACK", "WEBSEARCH", "ADAPTIVE"]:
            method = "ADAPTIVE"
        
        return method
    
    def process_query(self, query: str, vectorstore) -> Dict:
        """Auto-select and process with best method"""
        method = self.select_best_method(query)
        
        if method == "CORRECTIVE":
            result = self.corrective.process_query(query, vectorstore)
            result["method"] = "Corrective RAG"
        elif method == "FALLBACK":
            result = self.fallback.process_query(query, vectorstore)
            result["method"] = "Fallback RAG"
        elif method == "WEBSEARCH":
            result = self.websearch.process_query(query, vectorstore)
            result["method"] = "Web Search RAG"
        else:
            result = self.adaptive.process_query(query, vectorstore)
            result["method"] = "Adaptive RAG"
        
        return result

# Helper functions
def process_uploaded_files(uploaded_files, chunk_size=1000, chunk_overlap=200):
    """Process uploaded PDF or text files and create vectorstore"""
    try:
        all_documents = []
        files_info = []
        
        for uploaded_file in uploaded_files:
            file_extension = uploaded_file.name.split('.')[-1].lower()
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_extension}') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_file_path = tmp_file.name
            
            try:
                # Load based on file type
                if file_extension == 'pdf':
                    loader = PyPDFLoader(tmp_file_path)
                    documents = loader.load()
                    files_info.append({
                        'name': uploaded_file.name,
                        'type': 'PDF',
                        'pages': len(documents)
                    })
                elif file_extension in ['txt', 'text']:
                    loader = TextLoader(tmp_file_path)
                    documents = loader.load()
                    files_info.append({
                        'name': uploaded_file.name,
                        'type': 'Text',
                        'pages': len(documents)
                    })
                else:
                    st.warning(f"⚠️ Unsupported file type: {uploaded_file.name}")
                    continue
                
                all_documents.extend(documents)
                
            finally:
                # Clean up temporary file
                os.unlink(tmp_file_path)
        
        if not all_documents:
            st.error("❌ No valid documents found!")
            return None, [], []
        
        # Split documents into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        chunks = text_splitter.split_documents(all_documents)
        
        # Create embeddings and vectorstore
        embeddings = OpenAIEmbeddings()
        
        # Create persistent Chroma vectorstore
        persist_directory = tempfile.mkdtemp()
        vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=persist_directory,
            collection_name="uploaded_docs"
        )
        
        return vectorstore, chunks, files_info
        
    except Exception as e:
        st.error(f"❌ Error processing files: {str(e)}")
        return None, [], []

def create_sample_vectorstore():
    """Create sample vectorstore with default documents"""
    documents = [
        "Machine learning is a subset of AI that enables computers to learn from data without explicit programming.",
        "Overfitting occurs when a model learns training data too well, including noise and outliers.",
        "Overfitting leads to poor generalization on new data and high variance in predictions.",
        "To prevent overfitting, use techniques like regularization, cross-validation, and dropout.",
        "Cross-validation helps assess model performance and detect overfitting by testing on unseen data.",
        "Neural networks consist of layers of interconnected nodes that process information.",
        "Deep learning uses multiple layers to progressively extract higher-level features from data.",
        "Gradient descent is an optimization algorithm used to minimize the loss function in machine learning.",
        "Supervised learning uses labeled data to train models for classification and regression tasks.",
        "Unsupervised learning finds patterns in unlabeled data through clustering and dimensionality reduction."
    ]
    
    embeddings = OpenAIEmbeddings()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    
    # Create documents
    from langchain.schema import Document
    docs = [Document(page_content=doc) for doc in documents]
    
    # Create vectorstore
    persist_directory = tempfile.mkdtemp()
    vectorstore = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        persist_directory=persist_directory,
        collection_name="sample_docs"
    )
    
    return vectorstore, documents

# Main UI
st.markdown('<h1 class="main-header">🚀 Unified RAG System</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">5 Powerful RAG Strategies in One Intelligent System</p>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ RAG Configuration")
    
    # RAG Type Selection
    rag_type = st.selectbox(
        "Select RAG Type",
        ["Corrective RAG", "Fallback RAG", "Web Search RAG", "Adaptive RAG", "Unified System"],
        help="Choose which RAG strategy to use"
    )
    
    # Display badge
    badge_map = {
        "Corrective RAG": "badge-corrective",
        "Fallback RAG": "badge-fallback",
        "Web Search RAG": "badge-websearch",
        "Adaptive RAG": "badge-adaptive",
        "Unified System": "badge-unified"
    }
    st.markdown(f'<span class="info-badge {badge_map[rag_type]}">{rag_type}</span>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Dynamic parameters based on RAG type
    st.subheader("📊 Parameters")
    
    if rag_type == "Corrective RAG":
        st.markdown('<div class="parameter-section">', unsafe_allow_html=True)
        max_attempts = st.slider("Max Correction Attempts", 1, 5, 3)
        quality_threshold = st.select_slider(
            "Quality Threshold",
            options=["POOR", "AVERAGE", "GOOD", "EXCELLENT"],
            value="GOOD"
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
    elif rag_type == "Fallback RAG":
        st.markdown('<div class="parameter-section">', unsafe_allow_html=True)
        st.info("5 Fallback Levels Configured:")
        for i in range(1, 6):
            st.text(f"Level {i}: k={5*i}, threshold={0.8-i*0.1:.1f}")
        st.markdown('</div>', unsafe_allow_html=True)
        
    elif rag_type == "Web Search RAG":
        st.markdown('<div class="parameter-section">', unsafe_allow_html=True)
        use_internal = st.checkbox("Use Internal Knowledge", value=True)
        use_web = st.checkbox("Use Web Search", value=True)
        combine_results = st.checkbox("Combine Results", value=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    elif rag_type == "Adaptive RAG":
        st.markdown('<div class="parameter-section">', unsafe_allow_html=True)
        st.info("Auto-adjusts based on:")
        st.text("• Query Complexity")
        st.text("• User Level")
        st.text("• Topic Analysis")
        st.markdown('</div>', unsafe_allow_html=True)
        
    else:  # Unified System
        st.markdown('<div class="parameter-section">', unsafe_allow_html=True)
        st.success("Auto-selects best method!")
        st.text("Available methods:")
        st.text("✓ Corrective RAG")
        st.text("✓ Fallback RAG")
        st.text("✓ Web Search RAG")
        st.text("✓ Adaptive RAG")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Model settings
    st.subheader("🤖 Model Settings")
    model_name = st.text_input("Model", value="gpt-4o-mini", disabled=True)
    temperature = st.slider("Temperature", 0.0, 1.0, 0.7, 0.1)
    
    st.markdown("---")
    
    # Data Ingestion Section
    st.subheader("📁 Data Ingestion")
    
    data_source_option = st.radio(
        "Choose Data Source",
        ["Upload Files", "Use Sample Data"],
        help="Upload your own PDF/Text files or use sample ML data"
    )
    
    if data_source_option == "Upload Files":
        st.markdown("**Upload PDF or Text Files**")
        uploaded_files = st.file_uploader(
            "Choose files",
            type=['pdf', 'txt', 'text'],
            accept_multiple_files=True,
            help="Upload one or more PDF or text files"
        )
        
        # Chunking parameters
        with st.expander("⚙️ Chunking Parameters"):
            chunk_size = st.slider("Chunk Size", 500, 2000, 1000, 100)
            chunk_overlap = st.slider("Chunk Overlap", 0, 500, 200, 50)
        
        if uploaded_files:
            if st.button("🚀 Process Files"):
                with st.spinner(f"Processing {len(uploaded_files)} file(s)..."):
                    vectorstore, chunks, files_info = process_uploaded_files(
                        uploaded_files, 
                        chunk_size=chunk_size,
                        chunk_overlap=chunk_overlap
                    )
                    
                    if vectorstore:
                        st.session_state.vectorstore = vectorstore
                        st.session_state.chunk_count = len(chunks)
                        st.session_state.uploaded_files_info = files_info
                        st.session_state.data_source = "uploaded"
                        
                        st.success(f"✅ Processed {len(files_info)} file(s) into {len(chunks)} chunks!")
                        
                        # Display file info
                        for info in files_info:
                            st.info(f"📄 {info['name']} ({info['type']}) - {info['pages']} page(s)")
    
    else:  # Use Sample Data
        if st.button("🔄 Initialize Sample Data"):
            with st.spinner("Creating sample vectorstore..."):
                vectorstore, docs = create_sample_vectorstore()
                st.session_state.vectorstore = vectorstore
                st.session_state.documents = docs
                st.session_state.chunk_count = len(docs)
                st.session_state.data_source = "sample"
                st.success(f"✅ Loaded {len(docs)} sample documents!")
    
    # Display current data source info
    if st.session_state.data_source:
        st.markdown("---")
        st.markdown("**📊 Current Data Source**")
        
        if st.session_state.data_source == "uploaded":
            st.markdown(f"""
            <div class="metric-box">
                <h4>📁 Uploaded Files</h4>
                <p><strong>Files:</strong> {len(st.session_state.uploaded_files_info)}</p>
                <p><strong>Chunks:</strong> {st.session_state.chunk_count}</p>
                <p><strong>Status:</strong> ✅ Ready</p>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander("📋 File Details"):
                for info in st.session_state.uploaded_files_info:
                    st.text(f"• {info['name']} ({info['type']}) - {info['pages']} page(s)")
        
        elif st.session_state.data_source == "sample":
            st.markdown(f"""
            <div class="metric-box">
                <h4>🔬 Sample Data</h4>
                <p><strong>Documents:</strong> {st.session_state.chunk_count}</p>
                <p><strong>Topic:</strong> Machine Learning</p>
                <p><strong>Status:</strong> ✅ Ready</p>
            </div>
            """, unsafe_allow_html=True)
        
        if st.button("❌ Clear Data"):
            st.session_state.vectorstore = None
            st.session_state.documents = []
            st.session_state.chunk_count = 0
            st.session_state.uploaded_files_info = []
            st.session_state.data_source = None
            st.rerun()
    
    if st.button("🗑️ Clear Chat History"):
        st.session_state.chat_history = []
        st.rerun()
    
    st.markdown("---")
    
    # Statistics
    st.subheader("📈 Usage Statistics")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Corrective", st.session_state.stats['corrective'])
        st.metric("Fallback", st.session_state.stats['fallback'])
        st.metric("Web Search", st.session_state.stats['websearch'])
    with col2:
        st.metric("Adaptive", st.session_state.stats['adaptive'])
        st.metric("Unified", st.session_state.stats['unified'])

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("💬 Chat Interface")
    
    # Display chat history
    for msg in st.session_state.chat_history:
        if msg['role'] == 'user':
            st.markdown(f"""
            <div class="chat-message user-message">
                <strong>👤 You:</strong><br>
                {msg['content']}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="chat-message bot-message">
                <strong>🤖 Assistant ({msg.get('method', 'Unknown')}):</strong><br>
                {msg['content']}
            </div>
            """, unsafe_allow_html=True)
            
            # Show metadata
            if 'metadata' in msg:
                with st.expander("📊 Response Metadata"):
                    st.json(msg['metadata'])
    
    # Chat input
    with st.form(key='chat_form', clear_on_submit=True):
        user_query = st.text_area(
            "Your question:",
            placeholder="Ask anything about machine learning, AI, or any topic...",
            height=100
        )
        submit = st.form_submit_button("Send 🚀")
    
    if submit and user_query.strip():
        if st.session_state.vectorstore is None:
            st.warning("⚠️ Please upload files or initialize sample data first! Check the sidebar → Data Ingestion section.")
        else:
            # Add user message
            st.session_state.chat_history.append({
                'role': 'user',
                'content': user_query
            })
            
            # Process based on RAG type
            with st.spinner(f"Processing with {rag_type}..."):
                try:
                    if rag_type == "Corrective RAG":
                        rag = CorrectiveRAG()
                        result = rag.process_query(user_query, st.session_state.vectorstore, max_attempts)
                        st.session_state.stats['corrective'] += 1
                        
                    elif rag_type == "Fallback RAG":
                        rag = FallbackRAG()
                        result = rag.process_query(user_query, st.session_state.vectorstore)
                        st.session_state.stats['fallback'] += 1
                        
                    elif rag_type == "Web Search RAG":
                        rag = WebSearchRAG()
                        result = rag.process_query(user_query, st.session_state.vectorstore, use_internal)
                        st.session_state.stats['websearch'] += 1
                        
                    elif rag_type == "Adaptive RAG":
                        rag = AdaptiveRAG()
                        result = rag.process_query(user_query, st.session_state.vectorstore)
                        st.session_state.stats['adaptive'] += 1
                        
                    else:  # Unified System
                        rag = UnifiedRAGSystem()
                        result = rag.process_query(user_query, st.session_state.vectorstore)
                        st.session_state.stats['unified'] += 1
                    
                    # Add assistant response
                    metadata = {k: v for k, v in result.items() if k != 'answer'}
                    st.session_state.chat_history.append({
                        'role': 'assistant',
                        'content': result['answer'],
                        'method': result.get('method', rag_type),
                        'metadata': metadata
                    })
                    
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

with col2:
    st.subheader("📚 RAG Strategies")
    
    st.markdown("""
    <div class="rag-card">
        <h4>🔍 Corrective RAG</h4>
        <p>Evaluates quality, refines queries automatically</p>
        <small>Best for: Quality-critical queries</small>
    </div>
    
    <div class="rag-card">
        <h4>🔄 Fallback RAG</h4>
        <p>5 fallback levels ensure robust retrieval</p>
        <small>Best for: Difficult-to-answer queries</small>
    </div>
    
    <div class="rag-card">
        <h4>🌐 Web Search RAG</h4>
        <p>Combines internal + web search intelligently</p>
        <small>Best for: Current events, external info</small>
    </div>
    
    <div class="rag-card">
        <h4>🎯 Adaptive RAG</h4>
        <p>Adjusts to query complexity and user level</p>
        <small>Best for: Varied audience levels</small>
    </div>
    
    <div class="rag-card">
        <h4>🚀 Unified System</h4>
        <p>Auto-selects best method for each query</p>
        <small>Best for: General purpose use</small>
    </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <p>Built with ❤️ using Streamlit, LangChain & OpenAI</p>
    <p>🔑 API Keys: OPENAI_API_KEY, SERPAPI_API_KEY (from .env)</p>
</div>
""", unsafe_allow_html=True)
