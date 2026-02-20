import streamlit as st

def init_auth():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False


def login():
    st.session_state.logged_in = True
    st.rerun()


def logout():
    st.session_state.logged_in = False
    st.rerun()


def show_slave_login():
    SLAVE_USERNAME = st.secrets["slave_login"]["username"]
    SLAVE_PASSWORD = st.secrets["slave_login"]["password"]

    with st.expander("Slave Login (to edit tasks)"):
        uname = st.text_input("Username", key="login_uname")
        pwd = st.text_input("Password", type="password", key="login_pwd")
        
        if st.button("Login", use_container_width=True):
            if uname == SLAVE_USERNAME and pwd == SLAVE_PASSWORD:
                login()
            else:
                st.error("Incorrect credentials")


def show_logout_button():
    st.success("Logged in as Slave")
    if st.button("Logout", type="secondary"):
        logout()