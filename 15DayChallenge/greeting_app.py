import streamlit as st

# Set page title and icon
st.set_page_config(page_title="Greeting App", page_icon="👋")

# Add a title
st.title("Welcome to the Greeting App! 👋")

# Add a subtitle
st.write("Please enter your details below to get a personalized greeting.")

# Create two columns for better layoucdt
col1, col2 = st.columns(2)

# Get user name
with col1:
    user_name = st.text_input(
        "Enter your name:",
        placeholder="John Doe",
        help="Type your full name"
    )

# Get user age using slider
with col2:
    user_age = st.slider(
        "Select your age:",
        min_value=1,
        max_value=120,
        value=25,
        step=1,
        help="Use the slider to select your age"
    )

# Display greeting when name is provided
if user_name:
    st.success(f"### Hello, {user_name}! 🎉")
    
    # Add personalized message based on age
    if user_age < 13:
        st.info(f"You are {user_age} years old. Welcome, young friend! 🎈")
    elif user_age < 18:
        st.info(f"You are {user_age} years old. Welcome, teenager! 🎮")
    elif user_age < 65:
        st.info(f"You are {user_age} years old. Welcome, adult! 💼")
    else:
        st.info(f"You are {user_age} years old. Welcome, senior! 👴")
    
    # Display a summary card
    st.write("---")
    st.subheader("Your Information:")
    col_a, col_b = st.columns(2)
    with col_a:
        st.metric(label="Name", value=user_name)
    with col_b:
        st.metric(label="Age", value=user_age)
else:
    st.warning("👆 Please enter your name to get started!")

# Add footer
st.write("---")
st.caption("Made with ❤️ using Streamlit")
