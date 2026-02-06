# app/components/model_runner.py
import os
import numpy as np
from stable_baselines3 import PPO
from .irrigation_env import IrrigationEnv

# Load trained model
MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "ppo_irrigation_final")
model = PPO.load(MODEL_PATH)

def predict_daily_action(obs):
    """
    Given a dictionary of observations:
    {
        "crop": str,
        "soil": str,
        "soil_moisture": float,
        "temperature": float,
        "rain": float,
        "nutrients": [N, P, K]
    }
    Returns a single-step recommended action:
    - irrigation in liters
    - fertilizer in kg
    """
    # Create environment for 1-day prediction
    env = IrrigationEnv(days=1, crop=obs["crop"], soil=obs["soil"])
    
    # Reset environment with the current state
    env.set_state(
        soil_moisture=obs["soil_moisture"],
        temperature=obs["temperature"],
        rain=obs["rain"],
        nutrients=obs["nutrients"]
    )
    
    # Predict action
    action, _ = model.predict(env.get_observation(), deterministic=True)
    
    irrigation_liters = action[0] if len(action) > 0 else 0.0
    fertilizer_kg = action[1] if len(action) > 1 else 0.0
    
    return irrigation_liters, fertilizer_kg

def map_fertilizer(total_kg, obs):
    """
    Convert total fertilizer kg into N, P, K distribution.
    For simplicity, maintain same ratio as current nutrient indices.
    """
    N, P, K = obs["nutrients"]
    total = N + P + K
    if total == 0:
        return 0.0, 0.0, 0.0
    fert_N = total_kg * (N / total)
    fert_P = total_kg * (P / total)
    fert_K = total_kg * (K / total)
    return fert_N, fert_P, fert_K
