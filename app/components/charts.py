# app/components/charts.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- Current simple bar display (kept) ---
def display_soil_and_fertilizer_chart(soil, fertilizer):
    df = pd.DataFrame({
        "Metric": ["Soil Moisture", "Fertilizer Level"],
        "Value": [soil, fertilizer]
    })
    fig = px.bar(df, x="Metric", y="Value", color="Metric", text="Value",
                 title="🌾 Current Soil & Fertilizer Levels")
    st.plotly_chart(fig, use_container_width=True)

# --- Live simulation charts (kept) ---
def display_live_charts(history_df, rewards):
    if not history_df.empty:
        st.subheader("📊 Live Simulation Results")

        col1, col2 = st.columns(2)
        with col1:
            fig1 = px.line(history_df, x="Time", y="Soil Moisture", title="💧 Soil Moisture Over Time")
            fig1.update_xaxes(tickangle=45)
            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            fig2 = px.line(history_df, x="Time", y="Fertilizer", title="🌾 Fertilizer Levels Over Time")
            fig2.update_xaxes(tickangle=45)
            st.plotly_chart(fig2, use_container_width=True)

        if rewards:
            fig3 = px.line(x=list(range(len(rewards))), y=rewards, title="🏆 Reward Trend (AI Learning Progress)")
            fig3.update_layout(xaxis_title="Step", yaxis_title="Reward")
            st.plotly_chart(fig3, use_container_width=True)

# --- Manual mode charts / helpers ---
def plot_weather_trends_from_history(df):
    """Plot temp, rain over time from manual_history"""
    if df is None or df.empty:
        st.info("No history available to plot.")
        return
    st.markdown("**Temperature & Rainfall (recent)**")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["Time"], y=df["Temp"], mode="lines+markers", name="Temp (°C)"))
    fig.add_trace(go.Bar(x=df["Time"], y=df["Rain"], name="Rain (mm)", yaxis="y2", opacity=0.6))
    # add second y-axis
    fig.update_layout(
        title="Temperature and Rainfall",
        xaxis_tickangle=45,
        yaxis=dict(title="Temperature (°C)"),
        yaxis2=dict(title="Rain (mm)", overlaying="y", side="right")
    )
    st.plotly_chart(fig, use_container_width=True)

def plot_soil_vs_fertility(df):
    st.markdown("**Soil Moisture vs Fertilizer Level**")
    if df is None or df.empty:
        st.info("No data available.")
        return
    fig = px.line(df, x="Time", y=["Soil Moisture", "Fertilizer"], title="Soil Moisture and Fertilizer Over Time")
    fig.update_xaxes(tickangle=45)
    st.plotly_chart(fig, use_container_width=True)

def plot_irrigation_history(df):
    st.markdown("**Irrigation History**")
    if df is None or df.empty:
        st.info("No irrigation records.")
        return
    fig = px.bar(df, x="Time", y="Irrigation_L", title="Irrigation Applied Over Time")
    fig.update_xaxes(tickangle=45)
    st.plotly_chart(fig, use_container_width=True)

def plot_weather_summary(df):
    st.markdown("**Weather Summary**")
    if df is None or df.empty:
        st.info("No data available.")
        return
    # show mean temp, total rain as small cards
    mean_temp = df["Temp"].mean()
    total_rain = df["Rain"].sum()
    c1, c2 = st.columns(2)
    c1.metric("Avg Temp (recent)", f"{mean_temp:.1f} °C")
    c2.metric("Total Rain (recent)", f"{total_rain:.1f} mm")
    # small line chart for temps
    fig = px.line(df, x="Time", y="Temp", title="Temperature Trend")
    fig.update_xaxes(tickangle=45)
    st.plotly_chart(fig, use_container_width=True)
