from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize ChatOpenAI model
llm = ChatOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-3.5-turbo",
    temperature=0.7
)

# Create prompt template
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful AI assistant."),
    ("user", "{user_input}")
])

# Create chain using LCEL (LangChain Expression Language)
chain = prompt | llm

if __name__ == "__main__":
    user_input = input("Ask me anything: ")
    
    # Invoke the chain
    response = chain.invoke({"user_input": user_input})
    
    # Extract content from response
    print("AI says:", response.content)