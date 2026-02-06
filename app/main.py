# app/main.py
from db_utils import init_db

init_db()

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
from auth import init_db, create_user, verify_user, create_reset_token, reset_password
from dashboard import show_dashboard
from admin_dash import show_admin_dashboard
from landing import show_landing 

# ========================================================
# MAIN ENTRY POINT
# ========================================================
def main():
    st.set_page_config(page_title="Smart Farming AI", page_icon="🌾", layout="centered")
    init_db()

    # --- Session state initialization ---
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "page" not in st.session_state:
        st.session_state.page = "landing"  # Default to landing page

    # ========================================================
    # ROUTING LOGIC
    # ========================================================

    # 1️⃣ Landing page first (before login)
    if st.session_state.page == "landing" and not st.session_state.authenticated:
        show_landing()
        return

    # 2️⃣ If logged in → go to dashboard
    if st.session_state.authenticated:
        user = st.session_state.get("user")
        if user and user.get("role") == "admin":
            show_admin_dashboard()
        else:
            show_dashboard()
        return

    # 3️⃣ Authentication-related pages
    if st.session_state.page == "reset_request":
        show_reset_request()
    elif st.session_state.page == "reset_form":
        token = st.session_state.get("reset_token")
        show_reset_form(token)
    else:
        show_auth_page()


# ========================================================
# AUTHENTICATION PAGES
# ========================================================

def show_auth_page():
    """Displays Login / Signup UI with sidebar selection."""
    # st.title("Login / Signup")

    choice = st.sidebar.selectbox("Select Action", ["Login", "Sign up"])

    if choice == "Sign up":
        show_signup()
    else:
        show_login()

    # Back to landing
    st.markdown("---")
    if st.button("← Back to Home"):
        st.session_state.page = "landing"
        st.rerun()


def show_signup():
    st.subheader("Create Your Account")
    with st.form("signup_form"):
        name = st.text_input("Full name")
        username = st.text_input("Username")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        password2 = st.text_input("Confirm password", type="password")
        role = st.selectbox("Role", ["farmer", "admin"])
        submitted = st.form_submit_button("Create account")

    if submitted:
        if not all([name.strip(), username.strip(), email.strip(), password]):
            st.error("Please fill in all fields.")
        elif password != password2:
            st.error("Passwords do not match.")
        else:
            ok, err = create_user(name.strip(), username.strip(), email.strip(), password, role)
            if ok:
                st.success("✅ Account created successfully! You can now log in.")
            else:
                if "UNIQUE constraint failed: users.username" in (err or ""):
                    st.error("Username already taken.")
                elif "UNIQUE constraint failed: users.email" in (err or ""):
                    st.error("Email already used.")
                else:
                    st.error(f"Error creating account: {err}")


def show_login():
    st.subheader("Login to Your Account")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Login"):
            ok, user = verify_user(username, password)
            if ok:
                st.session_state.authenticated = True
                st.session_state.user = user
                st.success(f"Welcome {user['name']}! (Role: {user['role']})")
                st.rerun()
            else:
                st.error("Invalid username or password.")

    with col2:
        if st.button("Forgot Password?"):
            st.session_state.page = "reset_request"
            st.rerun()


def show_reset_request():
    st.subheader("🔑 Password Reset Request")
    user_input = st.text_input("Enter your username or email")

    if st.button("Send Reset Link"):
        token = create_reset_token(user_input)
        if token:
            st.session_state.reset_token = token
            reset_link = f"http://localhost:8501/?page=reset&token={token}"
            st.success("✅ Reset link generated!")
            st.info(f"(Demo) Use this link: {reset_link}")
        else:
            st.error("No user found with that username/email.")

    if st.button("← Back to Login"):
        st.session_state.page = None
        st.rerun()


def show_reset_form(token: str):
    st.subheader("🔐 Set a New Password")

    new_pw = st.text_input("New password", type="password")
    confirm_pw = st.text_input("Confirm password", type="password")

    if st.button("Reset Password"):
        if new_pw != confirm_pw:
            st.error("Passwords do not match.")
        elif reset_password(token, new_pw):
            st.success("✅ Password reset successful. Please log in again.")
            st.session_state.page = None
            st.rerun()
        else:
            st.error("Invalid or expired reset token.")


# ========================================================
# RUN APP
# ========================================================
if __name__ == "__main__":
    main()
