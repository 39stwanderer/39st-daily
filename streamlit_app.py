import streamlit as st
from components.auth import init_auth
from pages.home import main as home_main
from pages.add_training import main as add_main

init_auth()

# Define pages
home_page    = st.Page(home_main, title="Dashboard", icon="🏠", default=True)
add_page     = st.Page(add_main,  title="Add Training", icon="➕")

# Navigation (you control what appears)
pg = st.navigation({
    "Main": [home_page],
    "Actions": [add_page]
})

# Optional: show only if logged in, etc.
if not st.session_state.logged_in and pg != home_page:  # example
    pg = home_page

pg.run()