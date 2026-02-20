import streamlit as st
from components.auth import init_auth

# Must be first thing
init_auth()

# Simple routing using switch_page (Streamlit ≥ 1.28)
# If you're on older version, keep using session_state.page method

if 'page' not in st.session_state:
    st.session_state.page = "home"

# For first load / when no specific page requested
st.switch_page("pages/home.py")