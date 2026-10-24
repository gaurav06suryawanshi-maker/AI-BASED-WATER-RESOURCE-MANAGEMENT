"""
WaterGuard AI — AI-Based Water Resource Management System
Main Streamlit Application Entrypoint
"""
import streamlit as st

# Configure page setup
st.set_page_config(
    page_title="WaterGuard AI — Maharashtra",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply global styling
import config
from ui.styles import CUSTOM_CSS
from ui.components import render_header

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Initialize core services
from database.db import get_db
from simulation.sensor_simulator import SensorSimulator
from detection.engine import AnomalyDetectionEngine
from risk.scoring import RiskScoringEngine

db = get_db()
simulator = SensorSimulator(random_seed=42)
detection_engine = AnomalyDetectionEngine(db_manager=db)
risk_engine = RiskScoringEngine()

# Import view renderers
from ui.views.dashboard_view import render_dashboard_view
from ui.views.network_view import render_network_view
from ui.views.sensor_view import render_sensor_view
from ui.views.detection_view import render_detection_view
from ui.views.risk_view import render_risk_view
from ui.views.maintenance_view import render_maintenance_view
from ui.views.water_balance_view import render_water_balance_view
from ui.views.alerts_view import render_alerts_view
from ui.views.data_manager_view import render_data_manager_view
from ui.views.slides_view import render_slides_view
from ui.views.home_view import render_home_view

# Render Top App Header
render_header()

# --- Sidebar Navigation ---
st.sidebar.markdown("""
<div style="text-align: center; padding: 12px 0 20px 0;">
    <span style="font-size: 38px;">💧</span>
    <h2 style="margin: 4px 0 0 0; font-size: 20px; font-weight: 800; color: #0f172a; letter-spacing: -0.02em;">WaterGuard AI</h2>
    <div style="font-size: 13px; font-weight: 700; color: #0284c7; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 2px;">Maharashtra State Grid</div>
    <p style="margin: 4px 0 0 0; font-size: 12px; color: #64748b;">Smart Water Resources & Leak Intelligence</p>
</div>
""", unsafe_allow_html=True)

nav_options = [
    "🏠 Home: Every Drop Matters",
    "📊 Executive Dashboard",
    "🗺️ Pipeline Network Schematic & 3D Model",
    "📡 Simulated Sensor Telemetry",
    "🔍 Leak & Anomaly Detection",
    "⚖️ Risk-to-Response Intelligence",
    "🛠️ Predictive Maintenance",
    "💧 Water-Loss & Resource Analysis",
    "🚨 Alerts & Incident Triage",
    "💾 Data Management & Import/Export",
    "📚 Information Slides & Reference",
]

# Sync sidebar radio with session_state for programmatic navigation from home page cards
if "nav_selection" not in st.session_state or st.session_state["nav_selection"] not in nav_options:
    st.session_state["nav_selection"] = nav_options[0]

current_idx = nav_options.index(st.session_state["nav_selection"])

nav_page = st.sidebar.radio(
    "Navigation Menu",
    options=nav_options,
    index=current_idx,
    key="sidebar_nav_radio",
)

if nav_page != st.session_state["nav_selection"]:
    st.session_state["nav_selection"] = nav_page

st.sidebar.markdown("---")

# Sidebar Operational Status Overview
segments_count = len(db.get_all_segments())
alerts_count = len(db.get_alerts(status="ACTIVE"))
st.sidebar.markdown(f"""
<div style="font-size: 12px; color: #475569; padding: 0 5px;">
    <strong>System Health Summary:</strong><br>
    • Monitored Segments: <strong>{segments_count}</strong><br>
    • Active Incident Alerts: <strong style="color: {'#dc2626' if alerts_count > 0 else '#059669'};">{alerts_count}</strong><br>
    • Storage: <strong>SQLite (Local)</strong><br>
    • Engine Mode: <strong>Synthetic Physics</strong>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("---")
st.sidebar.caption("WaterGuard AI — Maharashtra • v1.1.0 • Built for Educational & Research Demonstration")

# --- Page Router ---
if nav_page == "🏠 Home: Every Drop Matters":
    render_home_view(db, simulator, detection_engine, risk_engine)

elif nav_page == "📊 Executive Dashboard":
    render_dashboard_view(db, simulator, detection_engine, risk_engine)

elif nav_page == "🗺️ Pipeline Network Schematic & 3D Model":
    render_network_view(db, simulator, detection_engine, risk_engine)

elif nav_page == "📡 Simulated Sensor Telemetry":
    render_sensor_view(db, simulator)

elif nav_page == "🔍 Leak & Anomaly Detection":
    render_detection_view(db, simulator, detection_engine)

elif nav_page == "⚖️ Risk-to-Response Intelligence":
    render_risk_view(db, simulator, detection_engine, risk_engine)

elif nav_page == "🛠️ Predictive Maintenance":
    render_maintenance_view(db, simulator, detection_engine, risk_engine)

elif nav_page == "💧 Water-Loss & Resource Analysis":
    render_water_balance_view(db, simulator)

elif nav_page == "🚨 Alerts & Incident Triage":
    render_alerts_view(db, detection_engine, simulator)

elif nav_page == "💾 Data Management & Import/Export":
    render_data_manager_view(db)

elif nav_page == "📚 Information Slides & Reference":
    render_slides_view()
