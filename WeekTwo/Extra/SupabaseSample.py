import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd

# Establish connection
conn = st.connection(
    "supabase",
    type=SupabaseConnection,
    url="https://zmayuqrdfavjihfjcgrg.supabase.co",
    key="sb_secret_aK49pK5Uh0ute8O1Qhj6KA_jcW0r4p4"
)

# Get the Supabase client
supabase = conn.client

# Query the "app_user" table
response = supabase.table("app_user").select("*").execute()

# Convert list of records to DataFrame
df = pd.DataFrame(response.data)

# Display as table
st.dataframe(df)