import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd

# Connect to Supabase
conn = st.connection(
    "supabase",
    type=SupabaseConnection,
    url="https://zmayuqrdfavjihfjcgrg.supabase.co",
    key="sb_secret_aK49pK5Uh0ute8O1Qhj6KA_jcW0r4p4"
)
supabase = conn.client

st.title("📋 Feedback Manager")

# --- Create ---
st.subheader("Add New Feedback")
with st.form("feedback_form"):
    name = st.text_input("Name")
    phone = st.text_input("Phone")
    email = st.text_input("Email")
    comments = st.text_area("Comments")
    submitted = st.form_submit_button("Submit")
    if submitted:
        supabase.table("feedback").insert({
            "name": name,
            "phone": phone,
            "email": email,
            "comments": comments
        }).execute()
        st.success("✅ Feedback submitted!")

# --- Read/Search ---
st.subheader("🔍 Search Feedback")
search_email = st.text_input("Search by Email")
if search_email:
    result = supabase.table("feedback").select("*").eq("email", search_email).execute()
    df = pd.DataFrame(result.data)
    st.dataframe(df)

# --- Update ---
st.subheader("✏️ Edit Feedback")
edit_id = st.text_input("Enter ID to Edit")
if edit_id:
    new_comment = st.text_area("New Comment")
    if st.button("Update Comment"):
        supabase.table("feedback").update({"comments": new_comment}).eq("id", int(edit_id)).execute()
        st.success("✅ Comment updated!")

# --- Delete ---
st.subheader("🗑️ Delete Feedback")
delete_id = st.text_input("Enter ID to Delete")
if delete_id and st.button("Delete Record"):
    supabase.table("feedback").delete().eq("id", int(delete_id)).execute()
    st.warning("⚠️ Record deleted.")