# app/dashboard.py
import streamlit as st

def show_dashboard():
    st.title("🌱 Smart Farming Dashboard")

    user = st.session_state.get("user")
    if user:
        st.markdown(f"👋 Welcome, **{user['name']}** (`{user['username']}`)")

    st.markdown("---")

    # Layout: Three metrics at the top
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🌤 Weather Forecast", "Rainy", "+5 mm")
    with col2:
        st.metric("💧 Irrigation Recommendation", "120 L/ha", "↓ 15%")
    with col3:
        st.metric("🌾 Fertilizer Recommendation", "15 kg/ha", "↓ 10%")

    st.markdown("---")

    # Charts section (currently placeholders)
    st.subheader("📈 Forecast Trends")
    st.info("Here you will later show graphs (e.g., rainfall prediction, temperature trends).")

    st.markdown("---")

    st.subheader("⚖️ With AI vs Without AI")
    st.info("Here you can add a comparison chart showing water saved, fertilizer saved, and yield improvement once your ML models are ready.")

    st.markdown("---")

    # Logout button
    if st.button("🚪 Logout"):
        for k in ["authenticated", "user"]:
            if k in st.session_state:
                del st.session_state[k]
        st.rerun()
