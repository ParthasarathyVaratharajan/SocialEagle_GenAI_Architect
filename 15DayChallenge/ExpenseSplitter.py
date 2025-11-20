import streamlit as st

st.set_page_config(page_title="Expense Splitter", layout="centered")
st.title("Expense Splitter — Split bills easily")

total = st.number_input("Total expense amount", min_value=0.0, value=0.0, step=0.01, format="%.2f")
n = st.number_input("Number of people", min_value=1, value=2, step=1)
st.markdown("Optional: enter names and contributions as comma-separated lists (leave blank to use defaults).")
names_txt = st.text_input("Names (comma-separated)", value="")
contribs_txt = st.text_input("Contributions (comma-separated, numbers)", value="")

def parse_list(text):
    return [s.strip() for s in text.split(",") if s.strip()]

def parse_floats(text):
    vals = []
    for s in text.split(","):
        s = s.strip()
        if not s:
            continue
        try:
            vals.append(float(s))
        except:
            vals.append(0.0)
    return vals

n = int(n)
names = parse_list(names_txt)
contribs = parse_floats(contribs_txt)

# Fill missing names and contributions
names = [names[i] if i < len(names) else f"Person {i+1}" for i in range(n)]
contribs = [contribs[i] if i < len(contribs) else 0.0 for i in range(n)]

if sum(contribs) and abs(sum(contribs) - total) > 0.01:
    st.info(f"Sum of contributions = {sum(contribs):.2f}. Total given = {total:.2f}. They don't match. App will still use the entered Total for share calculation.")
share = round(total / n, 2) if n else 0.0

rows = []
total_owed = 0.0
total_to_receive = 0.0
for i in range(n):
    c = round(contribs[i], 2)
    bal = round(c - share, 2)
    status = "Gets back" if bal > 0 else ("Owes" if bal < 0 else "Settled")
    if bal < 0:
        total_owed += -bal
    else:
        total_to_receive += bal
    rows.append({"Name": names[i], "Contributed": f"{c:.2f}", "Share": f"{share:.2f}", "Balance": f"{bal:.2f}", "Status": status})

st.subheader("Per-person breakdown")
st.table(rows)

st.subheader("Summary")
st.write(f"Equal share per person: **{share:.2f}**")
st.write(f"Total owed by people: **{total_owed:.2f}**")
st.write(f"Total to be reimbursed (should match): **{total_to_receive:.2f}**")

if total_owed and abs(total_owed - total_to_receive) > 0.01:
    st.warning("Totals don't match exactly. Check contributions or total amount for typos.")

owes = [r for r in rows if float(r["Balance"]) < 0]
receives = [r for r in rows if float(r["Balance"]) > 0]

if owes:
    st.subheader("Who owes money")
    for r in owes:
        st.write(f"{r['Name']}: owes {abs(float(r['Balance'])):.2f}")
if receives:
    st.subheader("Who gets reimbursed")
    for r in receives:
        st.write(f"{r['Name']}: gets {float(r['Balance']):.2f}")
if not owes and not receives:
    st.success("All settled. No one owes anything.")