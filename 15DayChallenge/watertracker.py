# water_tracker.py

import streamlit as st
import pandas as pd
import datetime
import matplotlib.pyplot as plt

st.set_page_config(page_title="💧 Water Intake Tracker", layout="centered")

st.title("💧 Daily Water Intake Tracker")
st.markdown("Track your hydration and progress toward the 3L daily goal.")

# Initialize session state
if "water_log" not in st.session_state:
    st.session_state.water_log = {}

# Log today's intake
today = datetime.date.today()
ml_input = st.number_input("Enter water intake (ml)", min_value=0, step=100)

if st.button("Log Intake"):
    st.session_state.water_log[str(today)] = st.session_state.water_log.get(str(today), 0) + ml_input
    st.success(f"Logged {ml_input} ml for {today}")

# Show today's progress
today_total = st.session_state.water_log.get(str(today), 0)
progress = min(today_total / 3000, 1.0)
st.metric("Today's Total", f"{today_total} ml")
st.progress(progress)

# Weekly hydration chart
st.subheader("📊 Weekly Hydration Chart")
last_7_days = [str(today - datetime.timedelta(days=i)) for i in range(6, -1, -1)]
weekly_data = {day: st.session_state.water_log.get(day, 0) for day in last_7_days}
df = pd.DataFrame(list(weekly_data.items()), columns=["Date", "Water (ml)"])

fig, ax = plt.subplots()
ax.bar(df["Date"], df["Water (ml)"], color="#00BFFF")
ax.axhline(3000, color="gray", linestyle="--", label="3L Goal")
ax.set_ylabel("Water Intake (ml)")
ax.set_title("Last 7 Days")
ax.legend()
plt.xticks(rotation=45)
st.pyplot(fig)