import streamlit as st
import requests

st.title("Streamlit ↔ n8n + Slack Demo")

user_input = st.text_input("Enter a message for Slack:")

if st.button("Send to Slack via n8n"):
    try:
        response = requests.post(
            "https://parthas79.app.n8n.cloud/webhook-test/streamlit-slack",  # replace with your n8n webhook URL
            json={"text": user_input}
        )
        if response.status_code == 200:
            st.success("Message sent to Slack successfully!")
        else:
            st.error(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        st.error(f"Request failed: {e}")