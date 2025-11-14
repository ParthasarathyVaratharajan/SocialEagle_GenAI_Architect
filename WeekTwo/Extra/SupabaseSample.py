import streamlit as st
from st_supabase_connection import SupabaseConnection

conn = st.connection("supabase", type=SupabaseConnection)

# Example: Fetch data from a table
data = conn.query("*", table="app_users")
st.write(data)