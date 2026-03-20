import streamlit as st
from db import verify_user


def render_auth_sidebar():
    if "user" in st.session_state and st.session_state["user"]:
        user = st.session_state["user"]
        st.sidebar.success(f"Logged in: {user['username']} ({user['role']})")
        if st.sidebar.button("Logout"):
            st.session_state.pop("user", None)
            st.session_state.pop("assessment_id", None)
            st.session_state.pop("_loaded_assessment_id", None)
            st.rerun()
        return user

    st.sidebar.title("Login")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")

    if st.sidebar.button("Login"):
        user = verify_user(username, password)
        if user:
            st.session_state["user"] = user
            st.success("Login successful.")
            st.rerun()
        else:
            st.error("Invalid username or password.")

    st.info("Default user: admin / admin")
    return None


def user_can_edit():
    user = st.session_state.get("user")
    return bool(user and user.get("role") in {"admin", "auditor"})


def user_is_admin():
    user = st.session_state.get("user")
    return bool(user and user.get("role") == "admin")
