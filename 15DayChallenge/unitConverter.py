# streamlit_unit_converter.py

import streamlit as st

st.set_page_config(page_title="Unit Converter", layout="centered")

st.title("🔄 Universal Unit Converter")
st.markdown("Convert between Currency, Temperature, Length, and Weight")

conversion_type = st.selectbox("Choose conversion type", ["Currency", "Temperature", "Length", "Weight"])

def convert_currency(amount, from_currency, to_currency, rate=83.0):
    if from_currency == "INR" and to_currency == "USD":
        return round(amount / rate, 2)
    elif from_currency == "USD" and to_currency == "INR":
        return round(amount * rate, 2)

def convert_temperature(value, from_unit, to_unit):
    if from_unit == "°C" and to_unit == "°F":
        return round((value * 9/5) + 32, 2)
    elif from_unit == "°F" and to_unit == "°C":
        return round((value - 32) * 5/9, 2)

def convert_length(value, from_unit, to_unit):
    if from_unit == "cm" and to_unit == "inch":
        return round(value / 2.54, 2)
    elif from_unit == "inch" and to_unit == "cm":
        return round(value * 2.54, 2)

def convert_weight(value, from_unit, to_unit):
    if from_unit == "kg" and to_unit == "lb":
        return round(value * 2.20462, 2)
    elif from_unit == "lb" and to_unit == "kg":
        return round(value / 2.20462, 2)

if conversion_type == "Currency":
    amount = st.number_input("Enter amount", min_value=0.0, format="%.2f")
    from_currency = st.selectbox("From", ["INR", "USD"])
    to_currency = st.selectbox("To", ["USD", "INR"])
    if st.button("Convert"):
        result = convert_currency(amount, from_currency, to_currency)
        st.success(f"{amount} {from_currency} = {result} {to_currency}")

elif conversion_type == "Temperature":
    value = st.number_input("Enter temperature", format="%.2f")
    from_unit = st.selectbox("From", ["°C", "°F"])
    to_unit = st.selectbox("To", ["°F", "°C"])
    if st.button("Convert"):
        result = convert_temperature(value, from_unit, to_unit)
        st.success(f"{value} {from_unit} = {result} {to_unit}")

elif conversion_type == "Length":
    value = st.number_input("Enter length", format="%.2f")
    from_unit = st.selectbox("From", ["cm", "inch"])
    to_unit = st.selectbox("To", ["inch", "cm"])
    if st.button("Convert"):
        result = convert_length(value, from_unit, to_unit)
        st.success(f"{value} {from_unit} = {result} {to_unit}")

elif conversion_type == "Weight":
    value = st.number_input("Enter weight", format="%.2f")
    from_unit = st.selectbox("From", ["kg", "lb"])
    to_unit = st.selectbox("To", ["lb", "kg"])
    if st.button("Convert"):
        result = convert_weight(value, from_unit, to_unit)
        st.success(f"{value} {from_unit} = {result} {to_unit}")