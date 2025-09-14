# app/main.py
import streamlit as st
from auth import init_db, create_user, verify_user
from dashboard import show_dashboard

def main():
    st.set_page_config(page_title="Smart Farming — Login", layout="centered")
    init_db()

    # session state flags
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        show_dashboard()
        return

    st.title("Smart Farming — Login / Signup")

    choice = st.sidebar.selectbox("Action", ["Login", "Sign up"])

    if choice == "Sign up":
        with st.form("signup_form"):
            name = st.text_input("Full name")
            username = st.text_input("Username")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            password2 = st.text_input("Confirm password", type="password")
            submitted = st.form_submit_button("Create account")

        if submitted:
            if not all([name.strip(), username.strip(), email.strip(), password]):
                st.error("Please fill in all fields.")
            elif password != password2:
                st.error("Passwords do not match.")
            else:
                ok, err = create_user(name.strip(), username.strip(), email.strip(), password)
                if ok:
                    st.success("Account created — you can now log in (switch to Login).")
                else:
                    if "UNIQUE constraint failed: users.username" in (err or ""):
                        st.error("Username already taken.")
                    elif "UNIQUE constraint failed: users.email" in (err or ""):
                        st.error("Email already used.")
                    else:
                        st.error(f"Error creating account: {err}")

    else:  # Login
        st.subheader("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            ok, user = verify_user(username, password)
            if ok:
                st.session_state.authenticated = True
                st.session_state.user = user
                st.success(f"Welcome {user['name']}!")
                st.rerun()
            else:
                st.error("Invalid username or password.")

if __name__ == "__main__":
    main()
