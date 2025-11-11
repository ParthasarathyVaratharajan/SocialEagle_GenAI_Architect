import streamlit as st
import sqlite3
import re
import pandas as pd

# 🔗 Connect to SQLite
conn = sqlite3.connect('directory.db', check_same_thread=False)
cursor = conn.cursor()

# 📜 Create table if not exists
cursor.execute('''
    CREATE TABLE IF NOT EXISTS contacts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT NOT NULL,
        email TEXT NOT NULL,
        comments TEXT
    )
''')
conn.commit()

# ───────────────────────────────
# 🧿 Initialize session state
for key in ["success_add", "success_manage", "reset_form"]:
    if key not in st.session_state:
        st.session_state[key] = ""

# ───────────────────────────────
# 🧭 Tabs
tab1, tab2 = st.tabs(["📝 Add Contact", "🔍 Manage Contacts"])

# ───────────────────────────────
# 📝 Tab 1: Add Contact
with tab1:
    st.header("Add New Contact")

    if st.session_state.success_add:
        st.success(st.session_state.success_add)
        st.session_state.success_add = ""

    if st.button("🆕 Create New"):
        st.session_state.reset_form = True
        st.rerun()

    if st.session_state.reset_form:
        st.session_state.name_input = ""
        st.session_state.phone_input = ""
        st.session_state.email_input = ""
        st.session_state.comments_input = ""
        st.session_state.reset_form = False

    name = st.text_input("Name", key="name_input")
    phone = st.text_input("Phone", key="phone_input")
    email = st.text_input("Email", key="email_input")
    comments = st.text_area("Comments", key="comments_input")

    def is_valid_email(email):
        return re.match(r"[^@]+@[^@]+\.[^@]+", email)

    def is_valid_phone(phone):
        return phone.isdigit() and len(phone) == 10

    if st.button("Add Contact"):
        if not name or not phone or not email:
            st.warning("⚠️ Name, Phone, and Email are required.")
        elif len(name) > 68:
            st.warning("⚠️ Name must not exceed 68 characters.")
        elif not is_valid_phone(phone):
            st.warning("⚠️ Phone must be exactly 10 digits.")
        elif not is_valid_email(email):
            st.warning("⚠️ Invalid email format.")
        elif len(comments) > 250:
            st.warning("⚠️ Comments must not exceed 250 characters.")
        else:
            cursor.execute("INSERT INTO contacts (name, phone, email, comments) VALUES (?, ?, ?, ?)",
                           (name, phone, email, comments))
            conn.commit()
            st.session_state.success_add = "✅ Contact added successfully."
            st.session_state.reset_form = True
            st.rerun()

# ───────────────────────────────
# 🔍 Tab 2: Manage Contacts
# ───────────────────────────────
# 🔍 Tab 2: Manage Contacts
with tab2:
    st.header("Search, Edit, or Delete Contacts")

    if st.session_state.success_manage:
        st.success(st.session_state.success_manage)
        st.session_state.success_manage = ""

    search_query = st.text_input("Search by name...")

    def load_contacts(search_query=""):
        if search_query:
            cursor.execute("""
                SELECT id, name, phone, email, comments
                FROM contacts
                WHERE name LIKE ?
                ORDER BY name ASC
            """, (f"%{search_query}%",))
        else:
            cursor.execute("SELECT id, name, phone, email, comments FROM contacts ORDER BY name ASC")
        return cursor.fetchall()

    data = load_contacts(search_query)

    if data:
        st.write("### Your Contacts")

        df = pd.DataFrame(data, columns=["ID", "Name", "Phone", "Email", "Comments"])
        df_display = df.drop(columns=["ID"])

        edited_df = st.data_editor(df_display, num_rows="dynamic", use_container_width=True)

        if st.button("💾 Save All Changes"):
            for i, row in edited_df.iterrows():
                contact_id = df.iloc[i]["ID"]
                cursor.execute("""
                    UPDATE contacts
                    SET name = ?, phone = ?, email = ?, comments = ?
                    WHERE id = ?
                """, (row["Name"], row["Phone"], row["Email"], row["Comments"], contact_id))
            conn.commit()
            st.session_state.success_manage = "💾 All changes saved successfully."
            st.rerun()

        st.write("### 🗑️ Delete a Contact")
        contact_names = df["Name"].tolist()
        selected_name = st.selectbox("Select contact to delete", contact_names)
        if st.button("Delete Selected"):
            selected_id = df[df["Name"] == selected_name]["ID"].values[0]
            cursor.execute("DELETE FROM contacts WHERE id = ?", (selected_id,))
            conn.commit()
            st.session_state.success_manage = f"🗑️ Contact '{selected_name}' successfully deleted."
            st.rerun()
    else:
        st.info("📭 No contacts found.")