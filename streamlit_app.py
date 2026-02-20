import streamlit as st
from components.auth import init_auth

init_auth()   # your session state setup

st.set_page_config(page_title="Slave Training Dashboard", layout="wide")

# Define pages (file paths relative to streamlit_app.py)
home_page = st.Page(
    "pages/home.py",
    title="Dashboard",
    icon="🏠",
    default=True   # lands here on first load
)

add_page = st.Page(
    "pages/add_training.py",
    title="Add Training",
    icon="➕"
)

# Grouped navigation (optional but clean)
pg = st.navigation({
    " ": [home_page],           # no header → top level
    "Actions": [add_page]
})

# Optional: hide sidebar if you don't want auto-navigation
# pg = st.navigation([home_page, add_page], position="hidden")

pg.run()