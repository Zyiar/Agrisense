import streamlit as st
import pandas as pd
import numpy as np
import joblib
import altair as alt
from pathlib import Path
from datetime import datetime, timedelta
# from app.db_utils import log_action  # Optional logging

# ===============================
# Paths
# ===============================
CURRENT_DIR = Path(__file__).resolve().parent
BASE_DIR = CURRENT_DIR.parent
MODELS_DIR = BASE_DIR / "models"

# ===============================
# Load Models
# ===============================
@st.cache_resource
def load_models():
    try:
        irrigation_model = joblib.load(MODELS_DIR / "irrigation_rf_model.pkl")
        fertilizer_model = joblib.load(MODELS_DIR / "fertilizer_rf_model.pkl")
        return irrigation_model, fertilizer_model
    except FileNotFoundError:
        st.warning("Model files not found. Using dummy models.")
        class DummyModel:
            def predict(self, X):
                if X.shape[1] < 10: return np.array([8.5])
                else: return np.array([35.0])
        return DummyModel(), DummyModel() 

# ===============================
# Agronomic Rule Helpers
# ===============================
def smooth_dryness_factor(soil_moisture_pct, field_capacity_pct=30.0):
    diff = max(0.0, field_capacity_pct - soil_moisture_pct)
    return np.clip(diff / 20.0, 0.0, 1.0)

def et0_scaling_factor(et0, baseline=3.0):
    factor = 1.0 + (et0 - baseline) * 0.08
    return float(np.clip(factor, 0.75, 1.5))

def rainfall_reduction_factor(rainfall_mm, saturation=12.0):
    factor = 1.0 - (rainfall_mm / saturation)
    return float(np.clip(factor, 0.0, 1.0))

def smooth_stage_factor(encoded_stage):
    x = float(encoded_stage)
    factor = np.exp(-((x - 2.5) ** 2) / 2.0)
    scaled = 0.5 + 0.7 * factor
    return float(np.clip(scaled, 0.4, 1.3))

def organic_matter_factor(om_pct):
    factor = 1.0 - (om_pct / 20.0)
    return float(np.clip(factor, 0.5, 1.0))

def ph_penalty_factor(soil_ph, optimal=6.5):
    penalty = 1.0 + (abs(optimal - soil_ph) * 0.05)
    return float(np.clip(penalty, 1.0, 1.3))

def cumulative_n_cap_factor(cum_n, soft_threshold=80.0, hard_reduction_start=120.0):
    if cum_n <= soft_threshold:
        return 1.0
    span = max(1.0, hard_reduction_start - soft_threshold)
    reduction = (cum_n - soft_threshold) / (span * 2.0)
    factor = 1.0 - reduction
    return float(np.clip(factor, 0.12, 1.0))

# ===============================
# Dashboard
# ===============================
def show_dashboard():
    st.set_page_config(page_title="Maize Precision Farming Dashboard", layout="wide")

    # --- CSS ---
    st.markdown("""
    <style>
    html, body, [class*="css"]  { font-family: 'Inter', sans-serif; }
    .block-container { padding: 1rem 2rem; max-width: 95%; }
    .section-header { font-size:1.4rem; font-weight:700; border-bottom:2px solid #4CAF50; color:#2E8B57; padding-bottom:5px; margin-top:2rem; margin-bottom:1rem; }
    .metric-card { border-radius:12px; padding:1.5rem 1rem; text-align:center; box-shadow:0 6px 15px rgba(0,0,0,0.08); transition: all 0.3s ease-in-out; border:1px solid #c0c0c0; color:#1e1e1e; font-weight:500; background:#F7FFF7; }
    .metric-card:hover { transform: translateY(-5px); box-shadow:0 8px 25px rgba(0,0,0,0.12); }
    .metric-label { font-size:1.0rem; margin-bottom:0.4rem; font-weight:600; color:#4CAF50; }
    .metric-value { font-size:2.0rem; font-weight:800; color:#004D40; }
    </style>
    """, unsafe_allow_html=True)

    # --- Header ---
    user = st.session_state.get("user", {"name": "Farmer", "username": "guest", "role": "Farmer"})
    if 'user' not in st.session_state:
        st.session_state['user'] = user

    col1, col2, col3 = st.columns([8, 0.5, 1])

    with col1:
        st.markdown('<div style="margin-top:30px;"><h2>🌽 Maize Precision Farming System (Hybrid ML)</h2></div>', unsafe_allow_html=True)

    with col2:
        initials = user.get("name", "User")[0].upper()
        st.markdown(
            f"""
            <div style="
                margin-top:30px;
                margin-left:auto;
                width: 40px;
                height: 40px;
                border-radius: 50%;
                background-color: #2E8B57;
                color: white;
                display: flex;
                justify-content: center;
                align-items: center;
                font-size: 1.2rem;
                font-weight: 700;">{initials}</div>
            """
        , unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div style="margin-top:30px;"></div>', unsafe_allow_html=True)
        with st.popover("Profile", use_container_width=False):
            st.markdown(
                f"**👤 {user.get('name','Guest')}** \n"
                f"**Username:** `{user.get('username','guest')}` \n"
                f"**Role:** {user.get('role','Farmer')}`"
            )
            st.divider()
            if st.button("Logout", use_container_width=True, key="logout_popover"):
                st.session_state.clear()
                st.rerun()

    st.markdown("<hr>", unsafe_allow_html=True)

    # --- Sidebar Inputs ---
    st.sidebar.header("🚀 Action & Status")
    default_inputs = {
        'soil_moisture':20.0, 'avg_temp':25.0, 'rainfall':2.0, 'et0':3.5, 
        'ndvi':0.75, 'humidity':65.0, 'wind':1.5, 'doy':datetime.today().timetuple().tm_yday,
        'plant_height':80.0, 'days_since_planting':40, 'lai':3.2, 
        'organic_matter':3.0, 'soil_ph':6.5, 'awc':60.0, 
        'cumulative_n':30.0, 'last_fert_days':10, 'irrigation_applied':5.0, 
        'growth_stage':"Vegetative"
    }
    for k,v in default_inputs.items():
        if k not in st.session_state:
            st.session_state[k] = v

    growth_stage = st.sidebar.selectbox("Current Growth Stage", ["Emergence", "Vegetative", "Flowering", "Grainfill", "Maturity"], key='growth_stage')
    run_button = st.sidebar.button("✨ Get Recommendations", use_container_width=True, type="primary")
    stage_order = {'Emergence':1,'Vegetative':2,'Flowering':3,'Grainfill':4,'Maturity':5}
    growth_stage_encoded = stage_order[growth_stage]

    # --- Expander for Detailed Inputs ---
    st.markdown('<div class="section-header">🔍 Field & Weather Data Input</div>', unsafe_allow_html=True)
    with st.expander("Adjust Sensor Readings & Field History", expanded=False):
        col_env, col_soil, col_crop = st.columns(3)
        with col_env:
            st.subheader("🌦️ Environmental & Weather")
            st.number_input("Average Temperature (°C)", 5.0, 40.0, st.session_state.avg_temp, key='avg_temp')
            st.number_input("Rainfall (mm)",0.0,200.0, st.session_state.rainfall, key='rainfall')
            st.number_input("ET0 (mm) - Evapotranspiration",0.0,10.0, st.session_state.et0, key='et0')
            st.number_input("Humidity (%)",0.0,100.0, st.session_state.humidity, key='humidity')
            st.number_input("Wind Speed (m/s)",0.0,20.0, st.session_state.wind, key='wind')
            st.number_input("Day of Year (DOY)",1,365, st.session_state.doy, key='doy')
        with col_soil:
            st.subheader("💧 Soil Conditions")
            st.number_input("Soil Moisture (% vol)",0.0,60.0, st.session_state.soil_moisture, key='soil_moisture')
            st.number_input("Organic Matter (%)",0.0,15.0, st.session_state.organic_matter, key='organic_matter')
            st.number_input("Soil pH",3.0,9.0, st.session_state.soil_ph, key='soil_ph')
            st.number_input("AWC (mm) - Available Water Capacity",20.0,300.0, st.session_state.awc, key='awc')
        with col_crop:
            st.subheader("🌱 Crop & History")
            st.number_input("NDVI - Crop Vigor Index",0.0,1.0, st.session_state.ndvi, key='ndvi')
            st.number_input("Plant Height (cm)",0.0,300.0, st.session_state.plant_height, key='plant_height')
            st.number_input("LAI - Leaf Area Index",0.0,10.0, st.session_state.lai, key='lai')
            st.number_input("Days Since Planting",0,200, st.session_state.days_since_planting, key='days_since_planting')
            st.number_input("Cumulative N Applied (kg/ha)",0.0,300.0, st.session_state.cumulative_n, key='cumulative_n')
            st.number_input("Days Since Last Fertilization",0,200, st.session_state.last_fert_days, key='last_fert_days')
            st.number_input("Irrigation Applied Yesterday (mm)",0.0,50.0, st.session_state.irrigation_applied, key='irrigation_applied')

    irrigation_model, fertilizer_model = load_models()
    current_inputs = {k: st.session_state[k] for k in default_inputs.keys() if k!='growth_stage'}

    # --- Run Predictions ---
    if run_button:
        soil_moisture = current_inputs['soil_moisture']
        avg_temp = current_inputs['avg_temp']
        rainfall = current_inputs['rainfall']
        et0 = current_inputs['et0']
        ndvi = current_inputs['ndvi']
        humidity = current_inputs['humidity']
        wind = current_inputs['wind']
        doy = current_inputs['doy']
        plant_height = current_inputs['plant_height']
        days_since_planting = current_inputs['days_since_planting']
        lai = current_inputs['lai']
        organic_matter = current_inputs['organic_matter']
        soil_ph = current_inputs['soil_ph']
        awc = current_inputs['awc']
        cumulative_n = current_inputs['cumulative_n']
        last_fert_days = current_inputs['last_fert_days']
        irrigation_applied = current_inputs['irrigation_applied']

        # ML Inputs
        X_irrigation = pd.DataFrame([{
            'Soil_Moisture_pct_vol': soil_moisture,'Avg_Temp_C': avg_temp,'Rainfall_mm': rainfall,
            'ET0_mm': et0,'NDVI': ndvi,'DOY': doy,'Wind_Speed_m_s': wind,'Humidity_%': humidity
        }])
        irrigation_ml = irrigation_model.predict(X_irrigation)[0]

        X_fertilizer = pd.DataFrame([{
            'Days_Since_Planting': days_since_planting,'Growth_Stage': growth_stage_encoded,
            'Plant_Height_cm': plant_height,'NDVI': ndvi,'LAI': lai,'Organic_Matter_%': organic_matter,
            'Soil_pH': soil_ph,'AWC_mm': awc,'Avg_Temp_C': avg_temp,'Rainfall_mm': rainfall,'Humidity_%': humidity,
            'Cumulative_N_applied_kg_ha': cumulative_n,'Last_Fertilization_DaysAgo': last_fert_days,
            'Soil_Moisture_pct_vol': soil_moisture,'ET0_mm': et0,'Irrigation_mm_applied': irrigation_applied
        }])
        fertilizer_ml = fertilizer_model.predict(X_fertilizer)[0]

        # --- Hybrid Agronomic Rules Applied ---
        # IRRIGATION
        dryness = smooth_dryness_factor(soil_moisture)
        et_factor = et0_scaling_factor(et0)
        rain_factor = rainfall_reduction_factor(rainfall)
        stage_modifier = smooth_stage_factor(growth_stage_encoded)/0.9
        base_rule = et0*stage_modifier + dryness*6.0
        irrigation_candidate = 0.5*irrigation_ml + 0.5*base_rule
        irrigation_candidate *= et_factor*rain_factor
        if avg_temp>30: irrigation_candidate*=1.05
        if humidity<40: irrigation_candidate*=1.05
        if irrigation_applied>15 and soil_moisture>25: irrigation_candidate*=0.6
        irrigation_output = float(np.clip(irrigation_candidate,0.0,30.0))

        # FERTILIZER
        stage_factor = smooth_stage_factor(growth_stage_encoded)
        om_factor = organic_matter_factor(organic_matter)
        ph_factor = ph_penalty_factor(soil_ph)
        cum_n_factor = cumulative_n_cap_factor(cumulative_n)
        seasonal_N_total = 150.0
        stage_shares={1:0.08,2:0.40,3:0.35,4:0.12,5:0.05}
        stage_share=stage_shares.get(growth_stage_encoded,0.2)
        rule_baseline_N = seasonal_N_total*stage_share*np.clip((ndvi*1.2 + plant_height/200.0),0.3,1.6)
        rule_candidate_N = rule_baseline_N*stage_factor*om_factor*ph_factor*cum_n_factor
        fertilizer_candidate = 0.45*fertilizer_ml + 0.55*rule_candidate_N
        if last_fert_days<7: fertilizer_candidate*=0.6
        fertilizer_output = float(np.clip(fertilizer_candidate,0.0,80.0))
        if growth_stage_encoded in [1,2]: fert_type="N fertilizer"
        elif growth_stage_encoded==3: fert_type="Balanced NPK"
        else: fert_type="Top-dressing / Maintenance"

        # --- Display Metrics ---
        st.markdown('<div class="section-header">✅ Daily Actionable Recommendations</div>', unsafe_allow_html=True)
        col1,col2 = st.columns(2)
        with col1:
            st.markdown(f'''
            <div class="metric-card" style="background:#E8F5E9;">
                <div class="metric-label">💧 Recommended Irrigation Volume</div>
                <div class="metric-value">{irrigation_output:.1f} mm</div>
                <p style="font-size:0.8rem; margin-top:0.5rem; color:#4A4A4A;">Current Stage: {growth_stage}</p>
            </div>
            ''',unsafe_allow_html=True)
        with col2:
            st.markdown(f'''
            <div class="metric-card" style="background:#FFF3E0;">
                <div class="metric-label">🌾 Recommended Fertilizer Amount ({fert_type})</div>
                <div class="metric-value">{fertilizer_output:.1f} kg/ha</div>
                <p style="font-size:0.8rem; margin-top:0.5rem; color:#4A4A4A;">Cumulative N applied: {cumulative_n:.1f} kg/ha</p>
            </div>
            ''',unsafe_allow_html=True)

        # --- Analytics Charts: Hybrid vs Rule ---
        rec_df=pd.DataFrame([
            {"type":"Irrigation (mm)","source":"ML Prediction","value":float(irrigation_ml)},
            {"type":"Irrigation (mm)","source":"Agronomic Rule","value":float(base_rule)},
            {"type":"Irrigation (mm)","source":"Final Output","value":float(irrigation_output)},
            {"type":"Fertilizer (kg/ha)","source":"ML Prediction","value":float(fertilizer_ml)},
            {"type":"Fertilizer (kg/ha)","source":"Agronomic Rule","value":float(rule_candidate_N)},
            {"type":"Fertilizer (kg/ha)","source":"Final Output","value":float(fertilizer_output)}
        ])
        rec_chart=alt.Chart(rec_df).mark_bar(opacity=0.8).encode(
            x=alt.X('source:N', sort=['ML Prediction','Agronomic Rule','Final Output']),
            y='value:Q',
            color=alt.Color('source:N', scale=alt.Scale(range=['#3498db','#f39c12','#2ecc71']), legend=None),
            column=alt.Column('type:N', header=alt.Header(titleOrient="bottom", labelOrient="top", labelPadding=10)),
            tooltip=['type:N','source:N','value:Q']
        ).properties(title="Hybrid Recommendation Synthesis: ML vs. Agronomic Logic").configure_title(fontSize=16)

        # --- Display Charts ---
        st.markdown('<div class="section-header">📈 Diagnostics and Justification</div>', unsafe_allow_html=True)
        st.altair_chart(rec_chart, use_container_width=True)

        # Crop Condition Radar (full-width below bar chart)
        metrics=["NDVI (Vigor)","Soil_Moisture (Water)","LAI (Canopy)","Stage (Demand)","Temp_Stress (Heat)","Water_Stress (E/R)"]
        ndvi_norm=np.clip((ndvi-0.2)/(0.8-0.2),0,1)
        sm_norm=np.clip((soil_moisture-15)/(35-15),0,1)
        lai_norm=np.clip((lai-0)/(6-0),0,1)
        stage_norm=(growth_stage_encoded-1)/4
        temp_stress=np.clip((avg_temp-25)/10,0,1)
        water_stress=np.clip((et0/6)*(1-rainfall/12),0,1)
        values=[ndvi_norm,sm_norm,lai_norm,stage_norm,temp_stress,water_stress]
        n=len(metrics)
        angles=np.linspace(0,2*np.pi,n,endpoint=False)
        radar_rows=[]
        for i,(m,v) in enumerate(zip(metrics,values)):
            angle=angles[i]
            radar_rows.append({"metric":m,"value":v,"x":v*np.cos(angle),"y":v*np.sin(angle),"angle":angle})
        radar_rows.append(radar_rows[0])
        radar_df=pd.DataFrame(radar_rows)
        radar_base=alt.Chart(radar_df).mark_line(point=True,color='#004D40').encode(
            x='x:Q',y='y:Q',tooltip=['metric:N',alt.Tooltip('value:Q',format='.2f')]
        ).properties(width=1100,height=400)
        text_layer=alt.Chart(radar_df.iloc[:-1]).mark_text(dx=20,dy=5).encode(
            x='x:Q',y='y:Q',text='metric:N',color=alt.value('gray')
        )
        radar_chart=(radar_base+text_layer).properties(title="🌿 Crop Status Diagnostic Wheel (Normalized)").configure_title(fontSize=16).configure_view(stroke=None)
        st.altair_chart(radar_chart, use_container_width=True)
        st.markdown("<p style='font-size:0.8rem;text-align:center;color:#555;'><i>The Diagnostic Wheel shows normalized health and stress metrics (0-1). Closer to center = higher stress.</i></p>", unsafe_allow_html=True)

        # --- 7-Day Simulated Trends ---
        st.markdown('<div class="section-header">🗓️ 7-Day Simulated Field Trends</div>', unsafe_allow_html=True)
        days=7
        end_date=datetime.now().date()
        dates=[end_date-timedelta(days=(days-1-i)) for i in range(days)]
        rng=np.random.default_rng(seed=42)
        sm_series=np.clip(soil_moisture + rng.normal(0,1.5,days).cumsum()*0.1,0,60)
        ndvi_series=np.clip(ndvi + rng.normal(0,0.02,days).cumsum()*0.02,0,1)
        et0_series=np.clip(et0 + rng.normal(0,0.1,days).cumsum()*0.05,0,10)
        temp_series=np.clip(avg_temp + rng.normal(0,0.5,days).cumsum()*0.2,5,45)
        trend_df=pd.DataFrame({"date":pd.to_datetime(dates),"Soil_Moisture":sm_series,"NDVI":ndvi_series,"ET0":et0_series,"Temp":temp_series})
        trend_melt=trend_df.melt(id_vars=["date"],var_name="metric",value_name="value")
        trend_chart=alt.Chart(trend_melt).mark_line(point=True).encode(
            x='date:T',y='value:Q',color='metric:N',tooltip=['date:T','metric:N','value:Q']
        ).properties(title="Key Parameter Projections (Demonstrative)")
        st.altair_chart(trend_chart,use_container_width=True)
    else:
        st.info("👆 Adjust inputs then press '✨ Get Recommendations' to run Hybrid ML and generate insights.")

if __name__=="__main__":
    show_dashboard()
