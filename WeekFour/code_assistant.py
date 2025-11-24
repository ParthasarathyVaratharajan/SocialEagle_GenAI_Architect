import os
import streamlit as st
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableSequence

# Load API key
load_dotenv()

# Initialize the model
llm = ChatOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4.1-mini",    # or gpt-4o
    temperature=0.5,
)

# Create the prompt template
prompt = PromptTemplate.from_template("""
You are a professional coding assistant. Help the user with this task:

{code_task}

Provide clean, well-commented code and explanations if needed.
""")

# Build the chain using LCEL (modern LangChain)
chain = prompt | llm

# ---------- Streamlit UI ----------
st.set_page_config(page_title="Code Assistant", page_icon="💻")
st.title("Code Assistant")

code_task = st.text_area("Describe your coding task:")

if st.button("Generate Code"):
    if not code_task.strip():
        st.warning("Please enter a task description.")
    else:
        with st.spinner("Generating code..."):
            result = chain.invoke({"code_task": code_task})

        st.subheader("Assistant Response")
        st.code(result.content, language="python")
