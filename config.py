"""
WaterGuard AI — Central System Configuration
Defines engineering parameters, operational thresholds, units, and system constants.
"""

from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "waterguard.db"
SAMPLE_DATA_DIR = BASE_DIR / "sample_data"

# Application Metadata
APP_TITLE = "WaterGuard AI — Maharashtra"
APP_SUBTITLE = "Smart Water-Resource Monitoring, Dam Telemetry & Pipeline Leak Intelligence"
VERSION = "1.1.0-MAHARASHTRA"
DISCLAIMER_TEXT = (
    "EDUCATIONAL & RESEARCH PROTOTYPE: All telemetry is generated via simulated physical models. "
    "Calculated discrepancies and risk assessments are for decision-support evaluation only. "
    "No autonomous valve or pump control is permitted."
)

# Standard Engineering Units
UNITS = {
    "pressure": "bar",
    "flow": "m³/h",
    "acoustic": "Index (0-100)",
    "vibration": "mm/s",
    "reservoir_level": "%",
    "reservoir_volume": "m³",
    "head_loss": "m",
    "velocity": "m/s",
}

# Hydraulic & Operational Thresholds
THRESHOLDS = {
    # Pressure (bar)
    "pressure_min_normal": 2.5,
    "pressure_max_normal": 6.5,
    "pressure_burst_drop_bar": 0.8,
    "pressure_surge_spike_bar": 1.2,
    
    # Flow & Mass Balance
    "meter_uncertainty_pct": 2.0,            # Standard electromagnetic / ultrasonic meter tolerance (±2%)
    "flow_imbalance_warning_pct": 5.0,        # Discrepancy > 5% triggers warning check
    "flow_imbalance_critical_pct": 12.0,      # Discrepancy > 12% indicates severe imbalance
    "min_flow_discrepancy_m3h": 15.0,         # Minimum volume deviation before flagging
    
    # Acoustic & Vibration
    "acoustic_normal_max": 25.0,              # Typical background pipe noise
    "acoustic_leak_threshold": 50.0,          # Elevated cavitation / leak hiss
    "acoustic_burst_threshold": 80.0,         # Severe structural breach or water turbulence
    "vibration_normal_max": 1.8,              # mm/s RMS
    "vibration_alert": 4.5,                   # mm/s RMS
    
    # Reservoir Levels (%)
    "reservoir_normal_min": 35.0,
    "reservoir_warning": 25.0,
    "reservoir_critical": 15.0,
    "reservoir_overfill_warning": 95.0,
    
    # Data Quality Bounds
    "pressure_physical_min": 0.0,             # Cannot be negative in gravity/pump feed without vacuum
    "pressure_physical_max": 16.0,            # Standard PN16 pipe rating
    "flow_physical_min": 0.0,
    "flow_physical_max": 1500.0,              # Max transmission capacity
    "max_frozen_consecutive_readings": 4,     # Readings with zero std-dev indicates stuck sensor
}

# Risk & Inspection Priority Weightings (Total = 100)
RISK_WEIGHTS = {
    "active_hydraulic_imbalance": 35,  # Flow loss + pressure drop
    "acoustic_evidence": 20,           # High frequency acoustic signature
    "asset_age_material": 20,          # Cast iron, old AC pipe vs modern ductile/HDPE
    "incident_history": 15,            # Repeat repair frequency on this segment
    "criticality_consequence": 10,     # Proximity to hospitals, reservoir mains, high-density areas
}

# Priority Tiers
PRIORITY_TIERS = {
    "NORMAL": {"range": (0, 29), "color": "#10B981", "badge": "Normal (Low Risk)"},
    "MONITOR": {"range": (30, 59), "color": "#F59E0B", "badge": "Monitor Closely"},
    "INSPECTION_RECOMMENDED": {"range": (60, 79), "color": "#F97316", "badge": "Inspection Recommended"},
    "URGENT_REVIEW": {"range": (80, 100), "color": "#EF4444", "badge": "Urgent Review Required"},
    "INSUFFICIENT_DATA": {"range": None, "color": "#6B7280", "badge": "Insufficient Data"},
}

# Water Journey Stages in Order
WATER_JOURNEY_STAGES = [
    "Source / Dam",
    "Water Treatment Plant",
    "Main Transmission Pipeline",
    "Monitoring Stations",
    "City Reservoirs",
    "Distribution Network",
]
