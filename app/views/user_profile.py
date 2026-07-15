import streamlit as st
from app.style import panel

def render() -> None:
    st.title("User Profile")
    st.markdown("View and edit your profile information here.")
    
    panel("Personal Details")
    
    # Using columns for layout
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("First Name", value="Jane")
        st.text_input("Email", value="jane@example.com")
    with col2:
        st.text_input("Last Name", value="Doe")
        st.text_input("Phone Number", value="+94 77 123 4567")
        
    st.button("Save Changes", type="primary")

    st.markdown("<br>", unsafe_allow_html=True)
    panel("Security")
    st.text_input("Current Password", type="password")
    st.text_input("New Password", type="password")
    st.text_input("Confirm New Password", type="password")
    st.button("Change Password")

    st.markdown("<br>", unsafe_allow_html=True)
    panel("Account Activity")
    st.info("No recent unusual activity detected on your account.")
