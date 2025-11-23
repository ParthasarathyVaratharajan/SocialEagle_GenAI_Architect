import streamlit as st
import tempfile
import os
from datetime import datetime
import json

# Page config
st.set_page_config(
    page_title="Knowledge Graph Document Intelligence",
    page_icon="🕸️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
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
    .graph-node {
        background: white;
        border: 2px solid #3b82f6;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .entity-badge {
        display: inline-block;
        background: #3b82f6;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        margin: 0.25rem;
    }
    .relationship-line {
        border-left: 3px solid #3b82f6;
        padding-left: 1rem;
        margin: 1rem 0;
    }
    .divider {
        height: 2px;
        background: linear-gradient(to right, transparent, #3b82f6, transparent);
        margin: 2rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'kg_data' not in st.session_state:
    st.session_state.kg_data = {
        'nodes': [],
        'relationships': [],
        'entities': {}
    }

# Header
st.markdown("""
<div class='main-header'>
    <h1 class='main-title'>🕸️ Knowledge Graph Document Intelligence</h1>
    <p class='main-subtitle'>AI-Powered Document Analysis with Knowledge Graph Visualization</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3774/3774299.png", width=100)
    st.markdown("### 🔐 System Configuration")
    
    # Import libraries
    try:
        from langchain_community.document_loaders import PyPDFLoader
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        from langchain_openai import ChatOpenAI, OpenAIEmbeddings
        from langchain_community.graphs import Neo4jGraph
        import networkx as nx
        import plotly.graph_objects as go
        
        st.success("✅ Libraries Loaded")
    except ImportError as e:
        st.error("❌ Missing Dependencies")
        st.code(str(e))
        st.stop()
    
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    
    # API Configuration
    st.markdown("### 🔑 API Configuration")
    
    try:
        OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", "")
        NEO4J_URI = st.secrets.get("NEO4J_URI", "")
        NEO4J_USER = st.secrets.get("NEO4J_USER", "neo4j")
        NEO4J_PASSWORD = st.secrets.get("NEO4J_PASSWORD", "")
        
        if OPENAI_API_KEY and NEO4J_URI and NEO4J_PASSWORD:
            st.success("✅ API Keys Configured")
        else:
            st.error("❌ API Keys Missing")
            st.info("""
            Required in `.streamlit/secrets.toml`:
            ```toml
            OPENAI_API_KEY = "sk-..."
            NEO4J_URI = "neo4j+s://..."
            NEO4J_USER = "neo4j"
            NEO4J_PASSWORD = "..."
            ```
            """)
            st.stop()
            
    except Exception as e:
        st.error(f"❌ Configuration Error: {str(e)}")
        st.stop()
    
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    
    # System Status
    st.markdown("### 📊 System Status")
    
    try:
        llm = ChatOpenAI(model="gpt-4o-mini", openai_api_key=OPENAI_API_KEY, temperature=0)
        st.success("✅ AI Model Active")
    except Exception as e:
        st.error(f"❌ AI Model Error: {str(e)}")
        st.stop()
    
    try:
        graph = Neo4jGraph(
            url=NEO4J_URI,
            username=NEO4J_USER,
            password=NEO4J_PASSWORD
        )
        st.success(f"✅ Neo4j Connected")
        
        # Get graph stats
        stats_query = """
        MATCH (n)
        RETURN count(n) as node_count
        """
        stats = graph.query(stats_query)
        node_count = stats[0]['node_count'] if stats else 0
        st.metric("Graph Nodes", node_count)
        
    except Exception as e:
        st.error(f"❌ Neo4j Error: {str(e)}")
        st.stop()
    
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    
    # Admin Controls
    st.markdown("### ⚙️ Admin Controls")
    
    if st.button("🗑️ Clear Graph Database", type="secondary", use_container_width=True):
        try:
            graph.query("MATCH (n) DETACH DELETE n")
            st.success("Graph cleared!")
            st.session_state.kg_data = {'nodes': [], 'relationships': [], 'entities': {}}
            st.rerun()
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()

# Main Content
tab1, tab2, tab3 = st.tabs(["📤 Document Upload", "🕸️ Knowledge Graph", "🔍 Query"])

with tab1:
    st.markdown("### 📤 Document Upload & Processing")
    
    uploaded_file = st.file_uploader(
        "Upload Document (PDF)",
        type=["pdf"],
        help="Upload a PDF document to build knowledge graph"
    )
    
    if uploaded_file:
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(uploaded_file.read())
                tmp_path = tmp_file.name
            
            with st.spinner("📖 Loading document..."):
                loader = PyPDFLoader(tmp_path)
                pages = loader.load_and_split()
                
                splitter = RecursiveCharacterTextSplitter(
                    chunk_size=500,
                    chunk_overlap=50
                )
                chunks = splitter.split_documents(pages)
            
            st.success(f"✅ Document processed: {len(chunks)} chunks")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Pages", len(pages))
            with col2:
                st.metric("Text Chunks", len(chunks))
            with col3:
                st.metric("File Size", f"{uploaded_file.size / 1024:.1f} KB")
            
            with st.spinner("🕸️ Building knowledge graph..."):
                # Clear existing graph
                graph.query("MATCH (n) DETACH DELETE n")
                
                # Insert chunks and extract entities
                for i, doc in enumerate(chunks):
                    # Create chunk node
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
                    
                    # Extract entities using LLM
                    entity_prompt = f"""Extract key entities from this text. Return a JSON with:
                    - entities: list of important entities (names, organizations, concepts)
                    - entity_types: type of each entity (PERSON, ORG, CONCEPT, etc.)
                    
                    Text: {doc.page_content[:300]}
                    
                    Return only valid JSON, no explanation."""
                    
                    try:
                        response = llm.invoke(entity_prompt)
                        entities_data = json.loads(response.content)
                        
                        if 'entities' in entities_data:
                            for entity in entities_data['entities'][:5]:  # Limit to 5 per chunk
                                entity_name = entity if isinstance(entity, str) else entity.get('name', '')
                                entity_type = 'ENTITY'
                                
                                if entity_name:
                                    # Create entity node
                                    graph.query(
                                        """
                                        MERGE (e:Entity {name: $name, type: $type})
                                        """,
                                        {"name": entity_name, "type": entity_type}
                                    )
                                    
                                    # Create relationship
                                    graph.query(
                                        """
                                        MATCH (c:Chunk {id: $chunk_id})
                                        MATCH (e:Entity {name: $entity_name})
                                        MERGE (c)-[:MENTIONS]->(e)
                                        """,
                                        {"chunk_id": f"chunk_{i}", "entity_name": entity_name}
                                    )
                    except:
                        pass  # Skip if entity extraction fails
                
                # Create sequential relationships between chunks
                for i in range(len(chunks) - 1):
                    graph.query(
                        """
                        MATCH (c1:Chunk {id: $id1})
                        MATCH (c2:Chunk {id: $id2})
                        MERGE (c1)-[:NEXT]->(c2)
                        """,
                        {"id1": f"chunk_{i}", "id2": f"chunk_{i+1}"}
                    )
            
            st.success("✅ Knowledge graph built successfully!")
            
            # Store graph data in session state
            nodes_result = graph.query("MATCH (n) RETURN n.id as id, n.name as name, n.content as content, labels(n)[0] as type")
            rels_result = graph.query("MATCH (a)-[r]->(b) RETURN a.id as source, type(r) as relationship, b.id as target, b.name as target_name")
            
            st.session_state.kg_data['nodes'] = nodes_result
            st.session_state.kg_data['relationships'] = rels_result
            
            # Cleanup
            try:
                os.unlink(tmp_path)
            except:
                pass
                
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            import traceback
            st.code(traceback.format_exc())

with tab2:
    st.markdown("### 🕸️ Knowledge Graph Visualization")
    
    if not st.session_state.kg_data['nodes']:
        st.info("📤 Upload a document first to build the knowledge graph")
    else:
        # Display graph statistics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Nodes", len(st.session_state.kg_data['nodes']))
        with col2:
            st.metric("Relationships", len(st.session_state.kg_data['relationships']))
        with col3:
            entity_count = sum(1 for n in st.session_state.kg_data['nodes'] if n.get('type') == 'Entity')
            st.metric("Entities", entity_count)
        
        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
        
        # Visualization options
        viz_type = st.radio(
            "Visualization Type",
            ["Network Graph", "Entity List", "Relationships Table"],
            horizontal=True
        )
        
        if viz_type == "Network Graph":
            st.markdown("#### 🔗 Interactive Network Visualization")
            st.info("💡 Hover over nodes to see chunk content and details")
            
            try:
                import plotly.graph_objects as go
                import networkx as nx
                
                # Create NetworkX graph
                G = nx.DiGraph()
                
                # Store node data for hover info
                node_data = {}
                
                # Add nodes with detailed information
                for node in st.session_state.kg_data['nodes']:
                    node_id = node.get('id') or node.get('name', 'unknown')
                    node_type = node.get('type', 'Unknown')
                    content = node.get('content', '')
                    page = node.get('page', 'N/A')
                    
                    G.add_node(node_id, type=node_type)
                    
                    # Store data for hover
                    node_data[node_id] = {
                        'type': node_type,
                        'content': content[:200] if content else node_id,
                        'page': page,
                        'full_content': content
                    }
                
                # Add edges
                edge_data = []
                for rel in st.session_state.kg_data['relationships']:
                    source = rel.get('source') or rel.get('source_name', '')
                    target = rel.get('target') or rel.get('target_name', '')
                    if source and target:
                        G.add_edge(source, target)
                        edge_data.append({
                            'source': source,
                            'target': target,
                            'type': rel.get('relationship', '')
                        })
                
                # Generate layout
                pos = nx.spring_layout(G, k=1, iterations=50, seed=42)
                
                # Create edge traces
                edge_x = []
                edge_y = []
                for edge in G.edges():
                    x0, y0 = pos[edge[0]]
                    x1, y1 = pos[edge[1]]
                    edge_x.extend([x0, x1, None])
                    edge_y.extend([y0, y1, None])
                
                edge_trace = go.Scatter(
                    x=edge_x, y=edge_y,
                    line=dict(width=1, color='#94a3b8'),
                    hoverinfo='none',
                    mode='lines',
                    showlegend=False
                )
                
                # Create node traces (separate by type for different colors)
                chunk_nodes_x = []
                chunk_nodes_y = []
                chunk_nodes_text = []
                chunk_nodes_hover = []
                
                entity_nodes_x = []
                entity_nodes_y = []
                entity_nodes_text = []
                entity_nodes_hover = []
                
                for node in G.nodes():
                    x, y = pos[node]
                    node_info = node_data.get(node, {})
                    node_type = node_info.get('type', 'Unknown')
                    
                    # Create hover text with full details
                    hover_text = f"<b>{node}</b><br>"
                    hover_text += f"Type: {node_type}<br>"
                    
                    if node_type == 'Chunk':
                        hover_text += f"Page: {node_info.get('page', 'N/A')}<br>"
                        hover_text += f"Content: {node_info.get('content', 'N/A')}<br>"
                        hover_text += "<i>(Click to see full content)</i>"
                        
                        chunk_nodes_x.append(x)
                        chunk_nodes_y.append(y)
                        chunk_nodes_text.append(node.split('_')[-1] if '_' in node else node[:10])
                        chunk_nodes_hover.append(hover_text)
                    else:  # Entity
                        hover_text += f"Entity: {node_info.get('content', node)}"
                        
                        entity_nodes_x.append(x)
                        entity_nodes_y.append(y)
                        entity_nodes_text.append(node[:15])
                        entity_nodes_hover.append(hover_text)
                
                # Chunk nodes trace (Green)
                chunk_trace = go.Scatter(
                    x=chunk_nodes_x, y=chunk_nodes_y,
                    mode='markers+text',
                    name='Chunks',
                    text=chunk_nodes_text,
                    textposition="top center",
                    hovertext=chunk_nodes_hover,
                    hoverinfo='text',
                    marker=dict(
                        size=20,
                        color='#10b981',
                        line=dict(width=2, color='white'),
                        symbol='circle'
                    ),
                    textfont=dict(size=8, color='black')
                )
                
                # Entity nodes trace (Blue)
                entity_trace = go.Scatter(
                    x=entity_nodes_x, y=entity_nodes_y,
                    mode='markers+text',
                    name='Entities',
                    text=entity_nodes_text,
                    textposition="top center",
                    hovertext=entity_nodes_hover,
                    hoverinfo='text',
                    marker=dict(
                        size=15,
                        color='#3b82f6',
                        line=dict(width=2, color='white'),
                        symbol='diamond'
                    ),
                    textfont=dict(size=8, color='black')
                )
                
                # Create figure
                fig = go.Figure(data=[edge_trace, chunk_trace, entity_trace],
                             layout=go.Layout(
                                title=dict(
                                    text='Knowledge Graph Network (Hover for Details)',
                                    font=dict(size=20)
                                ),
                                showlegend=True,
                                hovermode='closest',
                                margin=dict(b=20,l=5,r=5,t=40),
                                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                                plot_bgcolor='#f8fafc',
                                height=600,
                                legend=dict(
                                    orientation="h",
                                    yanchor="bottom",
                                    y=1.02,
                                    xanchor="right",
                                    x=1
                                )
                            ))
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Add legend explanation
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("🟢 **Green Circles** = Document Chunks")
                with col2:
                    st.markdown("🔷 **Blue Diamonds** = Extracted Entities")
                
            except Exception as e:
                st.error(f"Error creating visualization: {str(e)}")
                import traceback
                st.code(traceback.format_exc())
        
        elif viz_type == "Entity List":
            st.markdown("#### 📋 Extracted Entities")
            
            entities = [n for n in st.session_state.kg_data['nodes'] if n.get('type') == 'Entity']
            
            if entities:
                for entity in entities[:20]:  # Show first 20
                    entity_name = entity.get('name', 'Unknown')
                    st.markdown(f"""
                    <div class='graph-node'>
                        <span class='entity-badge'>{entity.get('type', 'ENTITY')}</span>
                        <strong>{entity_name}</strong>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No entities extracted yet")
        
        else:  # Relationships Table
            st.markdown("#### 🔗 Knowledge Graph Relationships")
            
            if st.session_state.kg_data['relationships']:
                for rel in st.session_state.kg_data['relationships'][:20]:
                    source = rel.get('source', 'Unknown')
                    target = rel.get('target_name') or rel.get('target', 'Unknown')
                    rel_type = rel.get('relationship', 'RELATED_TO')
                    
                    st.markdown(f"""
                    <div class='relationship-line'>
                        <strong>{source}</strong> 
                        <span style='color: #3b82f6;'>→ {rel_type} →</span> 
                        <strong>{target}</strong>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No relationships found")

with tab3:
    st.markdown("### 🔍 Knowledge Graph Query")
    
    query = st.text_area(
        "Ask a question about the document",
        placeholder="Example: What are the main topics discussed?",
        height=100
    )
    
    if st.button("🔍 Query Knowledge Graph", type="primary"):
        if query:
            try:
                with st.spinner("🔍 Searching knowledge graph..."):
                    # Search using Cypher
                    cypher_query = """
                    MATCH (c:Chunk)
                    WHERE toLower(c.content) CONTAINS toLower($query)
                    RETURN c.content AS content, c.page AS page
                    LIMIT 5
                    """
                    
                    results = graph.query(cypher_query, {"query": query})
                    
                    if results:
                        context = "\n\n".join([
                            f"[Page {r['page']}]\n{r['content']}"
                            for r in results
                        ])
                        
                        # Also get related entities
                        entity_query = """
                        MATCH (c:Chunk)-[:MENTIONS]->(e:Entity)
                        WHERE toLower(c.content) CONTAINS toLower($query)
                        RETURN DISTINCT e.name as entity
                        LIMIT 10
                        """
                        entities = graph.query(entity_query, {"query": query})
                        
                        prompt = f"""Based on the context below, answer the question.

Context:
{context}

Related Entities: {', '.join([e['entity'] for e in entities])}

Question: {query}

Provide a clear answer based on the context."""

                        response = llm.invoke(prompt)
                        answer = response.content
                        
                        st.markdown("### ✅ Answer")
                        st.success(answer)
                        
                        # Show related entities
                        if entities:
                            st.markdown("#### 🏷️ Related Entities")
                            entity_html = " ".join([
                                f"<span class='entity-badge'>{e['entity']}</span>"
                                for e in entities
                            ])
                            st.markdown(entity_html, unsafe_allow_html=True)
                        
                        # Show source chunks
                        with st.expander(f"📚 Source Chunks ({len(results)})"):
                            for i, r in enumerate(results, 1):
                                st.markdown(f"**Chunk {i}** (Page {r['page']})")
                                st.text(r['content'])
                                st.divider()
                    else:
                        st.warning("No relevant information found")
                        
            except Exception as e:
                st.error(f"❌ Query Error: {str(e)}")
                st.code(str(e))

# Footer
st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
st.markdown("""
<div style='text-align: center; color: #64748b; padding: 2rem;'>
    <p><strong>Knowledge Graph Document Intelligence System v1.0</strong></p>
    <p>🕸️ Graph-Powered | 🤖 AI-Enhanced | 🔍 Sparse/Lexical + Graph Traversal Search</p>
</div>
""", unsafe_allow_html=True)