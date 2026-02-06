# app/admin_dash.py
import streamlit as st
import pandas as pd
from pathlib import Path
from app.db_utils import get_connection, log_action, init_db

# --- Paths ---
MODELS_DIR = Path("models")

# --- Page config for wide layout ---
st.set_page_config(
    page_title="Admin Dashboard",
    layout="wide",
    initial_sidebar_state="auto"
)

# --- Reduce side padding & adjust title ---
st.markdown(
    """
    <style>
    .block-container {
        padding: 1rem 1rem;   /* top-bottom, left-right */
        max-width: 100%;
    }
    /* Reduce title size and add top margin */
    .main-title {
        font-size: 2rem !important;
        margin-top: 30px !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Initialize logs table ---
init_db()

# --- Admin Dashboard ---
def show_admin_dashboard():
    st.markdown('<h1 class="main-title">👨‍💼 Smart Farming — Admin Dashboard</h1>', unsafe_allow_html=True)
    user = st.session_state.get("user")
    if not user:
        st.error("No user logged in!")
        return

    st.markdown(f"Welcome, **{user['name']}** (`{user['username']}`) — Role: **{user['role']}**")
    st.markdown("---")

    # --- User Management ---
    st.subheader("🔍 User Management")
    conn = get_connection()
    users_df = pd.read_sql("SELECT * FROM users", conn)
    conn.close()

    st.dataframe(users_df)

    # Add / Remove User form below the table
    st.markdown("### Add / Remove User")
    new_name = st.text_input("Name")
    new_username = st.text_input("Username")
    new_role = st.selectbox("Role", ["farmer", "admin"])

    if st.button("Add User"):
        if new_username in users_df["username"].values:
            st.error("Username already exists!")
        else:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, name, role, last_login) VALUES (?, ?, ?, ?)",
                (new_username, new_name, new_role, "")
            )
            conn.commit()
            conn.close()
            log_action(user["username"], f"Added user: {new_username}")
            st.success(f"User {new_username} added!")
            st.experimental_rerun()

    remove_username = st.selectbox("Select user to remove", users_df["username"])
    if st.button("Remove User"):
        if remove_username == user["username"]:
            st.error("You cannot remove yourself!")
        else:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE username=?", (remove_username,))
            conn.commit()
            conn.close()
            log_action(user["username"], f"Removed user: {remove_username}")
            st.success(f"User {remove_username} removed!")
            st.experimental_rerun()

    # --- Model Monitoring ---
    st.markdown("---")
    st.subheader("📈 Model Performance")

    # Hardcoded R² values
    models_r2 = {
        "Irrigation Model": 0.848,
        "Fertilizer Model": 0.869
    }

    for name, r2 in models_r2.items():
        st.write(f"**{name}**")
        st.write(f"- Training Score (R²): {r2}")

    # --- System Logs ---
    st.markdown("---")
    st.subheader("⚙️ System Logs")
    conn = get_connection()
    try:
        logs_df = pd.read_sql("SELECT * FROM logs ORDER BY timestamp DESC", conn)
    except Exception:
        logs_df = pd.DataFrame(columns=["id","username","action","timestamp"])
    conn.close()

    username_filter = st.text_input("Filter by username")
    filtered_logs = logs_df
    if username_filter:
        filtered_logs = logs_df[logs_df["username"]==username_filter]
    st.dataframe(filtered_logs)

    # --- Logout ---
    st.markdown("---")
    if st.button("Logout"):
        for k in ["authenticated", "user"]:
            if k in st.session_state:
                del st.session_state[k]
        st.success("Logged out successfully. Please refresh or navigate to login page.")
        st.stop()  # stops execution, effectively “rerunning” when page reloads



# --- Run Dashboard ---
if __name__ == "__main__":
    show_admin_dashboard()
