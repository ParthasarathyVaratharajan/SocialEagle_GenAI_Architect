import streamlit as st


def calculate(operation: str, first: float, second: float) -> float:
    if operation == "Addition":
        return first + second
    if operation == "Subtraction":
        return first - second
    if operation == "Multiplication":
        return first * second
    if operation == "Division":
        if second == 0:
            raise ZeroDivisionError("Cannot divide by zero.")
        return first / second
    if operation == "Modulo":
        if second == 0:
            raise ZeroDivisionError("Cannot take modulo with zero.")
        return first % second
    if operation == "Power":
        return first**second
    raise ValueError(f"Unknown operation: {operation}")


st.set_page_config(page_title="Streamlit Calculator", page_icon="🧮", layout="centered")
st.title("Streamlit Calculator")
st.write("Select an operation and enter the numbers you want to calculate.")

col1, col2 = st.columns(2)
with col1:
    number_1 = st.number_input("First number", value=0.0, format="%.6f")
with col2:
    number_2 = st.number_input("Second number", value=0.0, format="%.6f")

operation = st.selectbox(
    "Operation",
    (
        "Addition",
        "Subtraction",
        "Multiplication",
        "Division",
        "Modulo",
        "Power",
    ),
)

if st.button("Calculate"):
    try:
        result = calculate(operation, number_1, number_2)
        st.success(f"Result: {result}")
    except ZeroDivisionError as division_error:
        st.error(str(division_error))
    except ValueError as value_error:
        st.error(str(value_error))

