# app/main.py
import streamlit as st
from auth import init_db, create_user, verify_user, create_reset_token, reset_password
from dashboard import show_dashboard

def main():
    st.set_page_config(page_title="Smart Farming — Login", layout="centered")
    init_db()

    # session state flags
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "page" not in st.session_state:
        st.session_state.page = None

    # If already logged in → dashboard
    if st.session_state.authenticated:
        show_dashboard()
        return

    # Normal login/signup/reset flow
    if st.session_state.page == "reset_request":
        show_reset_request()
    else:
        st.title("Smart Farming — Login / Signup")
        choice = st.sidebar.selectbox("Action", ["Login", "Sign up"])
        if choice == "Sign up":
            show_signup()
        else:
            show_login()

    # Handle reset link via query params
    query_params = st.query_params
    if query_params.get("page") == "reset" and "token" in query_params:
        token = query_params["token"][0]
        show_reset_form(token)

# --- UI helpers ---

def show_signup():
    with st.form("signup_form"):
        name = st.text_input("Full name")
        username = st.text_input("Username")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        password2 = st.text_input("Confirm password", type="password")
        role = st.selectbox("Role", ["farmer", "admin"])  # new role field
        submitted = st.form_submit_button("Create account")

    if submitted:
        if not all([name.strip(), username.strip(), email.strip(), password]):
            st.error("Please fill in all fields.")
        elif password != password2:
            st.error("Passwords do not match.")
        else:
            ok, err = create_user(name.strip(), username.strip(), email.strip(), password, role)
            if ok:
                st.success("Account created — you can now log in (switch to Login).")
            else:
                if "UNIQUE constraint failed: users.username" in (err or ""):
                    st.error("Username already taken.")
                elif "UNIQUE constraint failed: users.email" in (err or ""):
                    st.error("Email already used.")
                else:
                    st.error(f"Error creating account: {err}")

def show_login():
    st.subheader("Login")
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
            reset_link = f"http://localhost:8501/?page=reset&token={token}"
            st.success("Reset link generated!")
            st.info(f"(Demo only) Use this link: {reset_link}")
        else:
            st.error("No user found with that username/email.")

def show_reset_form(token: str):
    st.subheader("Set New Password")
    new_pw = st.text_input("New password", type="password")
    confirm_pw = st.text_input("Confirm password", type="password")
    if st.button("Reset Password"):
        if new_pw != confirm_pw:
            st.error("Passwords do not match.")
        elif reset_password(token, new_pw):
            st.success("Password reset successful. Please login again.")
            st.session_state.page = None
            st.rerun()
        else:
            st.error("Invalid or expired token.")

if __name__ == "__main__":
    main()
