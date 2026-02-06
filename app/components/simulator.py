# app/components/simulator.py
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

def get_recommendation(soil_moisture, temp, rain, nutrient):
    """
    Simple rule-based placeholder (later replaced by RL model).
    Returns irrigation in liters (L) and fertilizer in kg.
    """
    # Basic logic: more dry soil and less rain => more irrigation
    base_irrigation = max(0.0, 50 - (soil_moisture - rain * 0.5))
    irrigation = float(np.round(base_irrigation, 2))
    # Fertilizer: if nutrient index is low, recommend more
    fertilizer = float(np.round(max(0.0, (1.0 - nutrient) * 5), 2))
    return irrigation, fertilizer

def simulate_step(soil, fert):
    """
    Simulates a single time-step update.
    Returns new_soil, new_fert, irrigation_volume_L, fertilizer_kg, reward, temp, rain
    """
    # Simulate simple weather conditions
    temp = float(np.round(np.random.uniform(18.0, 32.0), 2))
    rain = float(np.round(np.random.uniform(0.0, 8.0), 2))  # mm

    # Agent decides irrigation and fertilizer (random for now)
    irrigation = float(np.round(np.random.uniform(0, 20), 2))  # liters applied this step
    fertilizer = float(np.round(np.random.uniform(0, 2), 2))  # kg applied this step

    # Update soil moisture: irrigation increases, rain increases, natural loss decreases
    soil_gain = irrigation * 0.2 + rain * 0.5
    soil_loss = np.random.uniform(0, 3)
    new_soil = min(100.0, max(0.0, soil + soil_gain - soil_loss))

    # Update fertilizer level (scale 0..1): fertilizer adds small amount, natural decline
    fert_gain = fertilizer * 0.01
    fert_loss = np.random.uniform(0, 0.02)
    new_fert = min(1.0, max(0.0, fert + fert_gain - fert_loss))

    # Simple reward: encourage moderate soil (not too dry, not flooded) and sufficient fert
    soil_score = 1.0 - abs(0.5 - (new_soil / 100.0))  # best when soil ~50%
    fert_score = new_fert  # higher is better up to 1.0
    reward = float(np.round(0.6 * soil_score + 0.4 * fert_score, 3))

    return new_soil, new_fert, irrigation, fertilizer, reward, temp, rain

# ---------------- Manual history helpers ----------------
def init_manual_history(init_soil=30.0, init_fert=0.6, steps=48):
    """
    Create an initial manual history dataframe (e.g., recent 48 records hourly)
    with synthetic realistic variations centered on init_soil/init_fert.
    """
    now = datetime.now()
    rows = []
    soil = init_soil
    fert = init_fert
    for i in range(steps):
        t = (now - timedelta(hours=(steps - i))).strftime("%Y-%m-%d %H:%M:%S")
        # small random walk
        soil = max(0.0, min(100.0, soil + np.random.uniform(-2, 2)))
        fert = max(0.0, min(1.0, fert + np.random.uniform(-0.01, 0.01)))
        irrigation = float(np.round(np.random.uniform(0, 10), 2))
        fert_kg = float(np.round(np.random.uniform(0, 0.5), 2))
        temp = float(np.round(np.random.uniform(18, 30), 2))
        rain = float(np.round(np.random.uniform(0, 4), 2))
        action = "None"
        rows.append({
            "Time": t,
            "Soil Moisture": soil,
            "Fertilizer": fert,
            "Irrigation_L": irrigation,
            "Fertilizer_kg": fert_kg,
            "Temp": temp,
            "Rain": rain,
            "Action": action
        })
    return pd.DataFrame(rows)

def append_manual_record(df, soil, fert, irrigation_l, fertilizer_kg, temp, rain, action=None):
    """Append a manual observation to manual_history DataFrame."""
    t = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    action_text = action if action is not None else f"Recorded (Irr:{irrigation_l}L / Fert:{fertilizer_kg}kg)"
    new_row = {
        "Time": t,
        "Soil Moisture": float(np.round(soil, 3)),
        "Fertilizer": float(np.round(fert, 3)),
        "Irrigation_L": float(np.round(irrigation_l, 3)),
        "Fertilizer_kg": float(np.round(fertilizer_kg, 3)),
        "Temp": float(np.round(temp, 2)),
        "Rain": float(np.round(rain, 2)),
        "Action": action_text
    }
    df = df.append(new_row, ignore_index=True)
    return df

def compute_manual_kpis(df):
    """
    Compute simple KPIs from manual history.
    Returns water_used (sum Irrigation_L) and fert_used (sum Fertilizer_kg).
    """
    if df is None or df.empty:
        return 0.0, 0.0
    water_used = float(df["Irrigation_L"].sum())
    fert_used = float(df["Fertilizer_kg"].sum())
    return water_used, fert_used
