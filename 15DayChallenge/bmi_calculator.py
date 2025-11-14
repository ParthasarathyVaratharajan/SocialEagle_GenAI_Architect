import streamlit as st

st.set_page_config(page_title="BMI Calculator", page_icon="🏋", layout="centered")
st.title("BMI Calculator 🏋")

height_cm = st.number_input("Height (cm)", min_value=0.0, value=170.0, step=0.1, format="%.1f")
weight_kg = st.number_input("Weight (kg)", min_value=0.0, value=70.0, step=0.1, format="%.1f")

def bmi_category(bmi: float) -> str:
    if bmi < 18.5:
        return "Underweight"
    if bmi < 25:
        return "Normal"
    if bmi < 30:
        return "Overweight"
    return "Obese"

if height_cm <= 0 or weight_kg <= 0:
    st.info("Enter positive height and weight to calculate BMI.")
else:
    h_m = height_cm / 100
    bmi = weight_kg / (h_m * h_m)
    b = round(bmi, 2)
    cat = bmi_category(bmi)
    st.metric("BMI", f"{b:.2f}")
    st.write(f"Category: **{cat}**")
    st.write("Ranges: Underweight (<18.5), Normal (18.5–24.9), Overweight (25–29.9), Obese (≥30)")
