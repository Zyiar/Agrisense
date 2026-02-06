import streamlit as st

def show_landing():
    st.set_page_config(page_title="Smart Farming AI", layout="centered")

    # --- Custom CSS ---
    st.markdown("""
        <style>
        .landing-container {
            text-align: center;
            margin-top: 100px;
        }
        .title {
            font-size: 2.5rem;
            font-weight: bold;
            color: #2E7D32;
        }
        .subtitle {
            font-size: 1.2rem;
            color: #555;
            margin-top: 10px;
        }
        .button-container {
            margin-top: 40px;  /* ✅ adds space before the button */
        }
        .footer {
            margin-top: 100px;
            font-size: 0.9rem;
            color: #777;
        }
        </style>
    """, unsafe_allow_html=True)

    # --- Title + Subtitle ---
    st.markdown("""
    <div class="landing-container">
        <div class="title">🌱 Smart Farming AI</div>
        <div class="subtitle">
            An intelligent system for optimizing irrigation and fertilizer use<br>
            using soil and weather data.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- Add spacing before button ---
    st.markdown("<div class='button-container'></div>", unsafe_allow_html=True)

    # --- Centered Button ---
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("Go to Login / Signup →", width="stretch", type="primary"):
            st.session_state["page"] = "auth"
            st.rerun()

    # --- Footer ---
    # st.markdown("<div class='footer'>© 2025 Smart Farming AI Project — Strathmore University</div>", unsafe_allow_html=True)
