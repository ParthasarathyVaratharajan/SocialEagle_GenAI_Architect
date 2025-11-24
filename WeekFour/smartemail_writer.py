import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import os

# Page configuration
st.set_page_config(
    page_title="Smart Email Writer",
    page_icon="📧",
    layout="wide"
)

# Title and description
st.title("📧 Smart Email Writer")
st.markdown("Generate professional emails using AI with customizable tone and purpose")

# Sidebar for API key and settings
with st.sidebar:
    st.header("⚙️ Settings")
    
    # API Key input
    api_key = st.text_input(
        "OpenAI API Key",
        type="password",
        help="Enter your OpenAI API key"
    )
    
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key
        st.success("API Key configured!")
    else:
        st.warning("Please enter your OpenAI API key to continue")
    
    st.divider()
    
    # Model selection
    model_name = st.selectbox(
        "Select Model",
        ["gpt-4", "gpt-3.5-turbo", "gpt-4-turbo"],
        index=1
    )
    
    temperature = st.slider(
        "Creativity Level",
        min_value=0.0,
        max_value=1.0,
        value=0.7,
        step=0.1,
        help="Higher values make output more creative"
    )

# Main content area
col1, col2 = st.columns([1, 1])

with col1:
    st.header("📝 Email Details")
    
    # Email purpose
    email_purpose = st.selectbox(
        "Email Purpose",
        [
            "Job Application",
            "Follow-up",
            "Introduction",
            "Meeting Request",
            "Thank You",
            "Apology",
            "Complaint",
            "Request for Information",
            "Networking",
            "Custom"
        ]
    )
    
    # Tone selection
    tone = st.selectbox(
        "Tone",
        [
            "Professional",
            "Friendly",
            "Formal",
            "Casual",
            "Enthusiastic",
            "Apologetic",
            "Assertive"
        ]
    )
    
    # Recipient information
    recipient_name = st.text_input("Recipient Name", placeholder="e.g., John Smith")
    
    # Email length
    length = st.select_slider(
        "Email Length",
        options=["Short", "Medium", "Long"],
        value="Medium"
    )
    
    # Key points
    st.subheader("Key Points to Include")
    key_points = st.text_area(
        "Enter the main points you want to cover",
        placeholder="e.g., Interested in the Software Engineer position\nHave 5 years of experience in Python\nAvailable for an interview next week",
        height=150
    )
    
    # Additional context
    additional_context = st.text_area(
        "Additional Context (Optional)",
        placeholder="Any additional information or specific requirements",
        height=100
    )

with col2:
    st.header("✉️ Generated Email")
    
    # Generate button
    if st.button("Generate Email", type="primary", use_container_width=True):
        if not api_key:
            st.error("Please enter your OpenAI API key in the sidebar")
        elif not key_points:
            st.error("Please enter at least one key point")
        else:
            try:
                with st.spinner("Generating your email..."):
                    # Initialize ChatOpenAI
                    llm = ChatOpenAI(
                        model=model_name,
                        temperature=temperature,
                        api_key=api_key
                    )
                    
                    # Create prompt template
                    template = """You are a professional email writing assistant. Generate a well-structured email based on the following information:

Purpose: {purpose}
Tone: {tone}
Recipient Name: {recipient}
Length: {length}
Key Points to Cover:
{key_points}

Additional Context:
{context}

Generate a complete email including:
- An appropriate subject line
- A proper greeting
- Well-organized body paragraphs
- A professional closing

Make sure the email is {tone} in tone and {length} in length. Do not include [Your Name] at the end - just end with the closing."""

                    prompt = ChatPromptTemplate.from_template(template)
                    
                    # Create chain using LCEL
                    chain = prompt | llm
                    
                    # Generate email
                    response = chain.invoke({
                        "purpose": email_purpose,
                        "tone": tone.lower(),
                        "recipient": recipient_name if recipient_name else "the recipient",
                        "length": length.lower(),
                        "key_points": key_points,
                        "context": additional_context if additional_context else "None"
                    })
                    
                    result = response.content
                    
                    # Store in session state
                    st.session_state.generated_email = result
                    st.success("Email generated successfully!")
                    
            except Exception as e:
                st.error(f"Error generating email: {str(e)}")
    
    # Display generated email
    if 'generated_email' in st.session_state:
        st.text_area(
            "Your Email",
            value=st.session_state.generated_email,
            height=400,
            key="email_output"
        )
        
        # Action buttons
        col_a, col_b, col_c = st.columns(3)
        
        with col_a:
            if st.button("📋 Copy to Clipboard", use_container_width=True):
                st.toast("Email copied to clipboard!")
        
        with col_b:
            if st.button("🔄 Regenerate", use_container_width=True):
                if 'generated_email' in st.session_state:
                    del st.session_state.generated_email
                st.rerun()
        
        with col_c:
            if st.button("🗑️ Clear", use_container_width=True):
                if 'generated_email' in st.session_state:
                    del st.session_state.generated_email
                st.rerun()
        
        # Download option
        st.download_button(
            label="⬇️ Download Email",
            data=st.session_state.generated_email,
            file_name="generated_email.txt",
            mime="text/plain",
            use_container_width=True
        )

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: gray; font-size: 0.9em;'>
    <p>💡 Tip: Be specific with your key points for better results</p>
    <p>Built with Streamlit, LangChain, and OpenAI</p>
</div>
""", unsafe_allow_html=True)