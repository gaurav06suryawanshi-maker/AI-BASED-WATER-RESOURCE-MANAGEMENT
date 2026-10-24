# WaterGuard AI — AI-Based Water Resource Management System
### *Smart Municipal Pipeline Telemetry, Multi-Indicator Leak Detection, and Risk-to-Response Intelligence Prototype*

---

## 📌 Executive Overview

**WaterGuard AI** is a smart water-resource monitoring, anomaly intelligence, and pipeline-maintenance decision-support system. It simulates the complete municipal water journey:

$$\text{Water Source / Dam} \longrightarrow \text{Water Treatment Plant} \longrightarrow \text{Main Transmission Pipeline} \longrightarrow \text{Monitoring Stations} \longrightarrow \text{City Reservoirs} \longrightarrow \text{Distribution Network}$$

The system equips water utility engineers, operators, and maintenance dispatchers with explainable intelligence to:
- Identify hydraulic and acoustic anomalies across transmission and distribution networks.
- Discriminate genuine subsurface leaks and sudden pipeline bursts from sensor faults, demand surges, and permitted withdrawals.
- Calculate unexplained volumetric discrepancies using mass-balance conservation with rigorous meter uncertainty error propagation ($\pm 2\%$).
- Rank pipeline segments using an **explainable 0–100 Inspection Priority Index** that separates immediate telemetry alerts from long-term asset deterioration.
- Track maintenance work orders, assign personnel, log physical inspection findings, and manage incident resolution with persistent local SQLite storage.

> **Operational Notice:** *WaterGuard AI is an educational and research prototype. All telemetry is generated via simulated physical models. Anomaly scores and risk indexes are advisory decision-support tools rather than physical proof of pipe failure. It does not control physical municipal valves or pumps.*

---

## 🏗️ Architecture & Component Modularity

The application follows a strictly decoupled, production-grade modular design:

```
d:\ai based water resource management\
├── app.py                      # Main Streamlit application entrypoint & page router
├── config.py                   # Central configuration, engineering thresholds, and units
├── requirements.txt            # Python dependencies (Streamlit, Pandas, Plotly, etc.)
├── waterguard.db               # SQLite local persistent database (auto-initialized)
│
├── database/                   # Local Database Layer
│   ├── __init__.py
│   └── db.py                   # SQLite connection manager, tables, migrations, queries
│
├── models/                     # Strongly Typed Domain Models
│   ├── __init__.py
│   ├── pipeline.py             # PipelineSegment, WaterSource, Reservoir, Station
│   ├── sensor.py               # SensorReading, SensorType, SensorHealthStatus
│   ├── alert.py                # Alert, IncidentStatus, AlertSeverity, AlertCategory
│   └── maintenance.py          # MaintenanceRecord, InspectionFinding, WorkOrder
│
├── simulation/                 # Physical Simulation Engine
│   ├── __init__.py
│   ├── network_topology.py     # Schematic coordinates & pipeline connectivity
│   ├── sensor_simulator.py     # Diurnal curves & hydraulic telemetry generator
│   └── scenarios.py            # 9 deterministic operational simulation scenarios
│
├── detection/                  # Multi-Indicator Detection Engine
│   ├── __init__.py
│   ├── quality_filter.py       # Screens missing, frozen, delayed, & unrealistic data
│   ├── water_balance.py        # Mass-balance ($Q_{in} - Q_{out} - \Delta S - W_{auth}$) & uncertainty
│   ├── hydraulic_analysis.py   # Pressure gradient vs Hazen-Williams friction
│   ├── acoustic_analysis.py    # Acoustic hiss & turbulent vibration analysis
│   └── engine.py               # Cross-validates modalities to eliminate false alarms
│
├── risk/                       # Risk-to-Response Intelligence (Key Feature)
│   ├── __init__.py
│   ├── scoring.py              # 0–100 Explainable Inspection Priority Index
│   └── recommendations.py      # Plain-language engineering advisory actions
│
├── ui/                         # Modern Professional Interface
│   ├── __init__.py
│   ├── styles.py               # CSS design tokens, accessible status badges, cards
│   ├── components.py           # Header, metric cards, Plotly styling helpers
│   └── views/                  # Dedicated views for each functional module
│       ├── dashboard_view.py       # Executive overview & scenario switcher
│       ├── network_view.py         # Interactive Plotly schematic graph
│       ├── sensor_view.py          # Real-time multi-modal telemetry streams
│       ├── detection_view.py       # Multi-indicator evidence matrix & alerts
│       ├── risk_view.py            # Inspection priority league table & breakdown
│       ├── maintenance_view.py     # Work orders & inspection findings log
│       ├── water_balance_view.py   # Mass-balance audit & uncertainty charts
│       ├── alerts_view.py          # Incident triage, acknowledgement & resolution
│       └── data_manager_view.py    # CSV import/export & demo reset
│
├── sample_data/                # Validated CSV Templates
│   ├── pipeline_assets_sample.csv
│   ├── sensor_readings_sample.csv
│   └── maintenance_history_sample.csv
│
└── tests/                      # Automated Pytest Suite (25 Tests)
    ├── __init__.py
    ├── test_simulation.py
    ├── test_water_balance.py
    ├── test_detection.py
    ├── test_risk_scoring.py
    ├── test_database.py
    └── test_csv_handler.py
```

---

## 🚀 Installation & Run Guide (Windows 11)

### 1. Prerequisites
- **Windows 11** (or Windows 10)
- **Python 3.10+** (Python 3.11.9 tested and verified)
- **PowerShell** or **Command Prompt**

### 2. Verify or Install Python
Open Windows PowerShell:
```powershell
python --version
pip --version
```

### 3. Navigate to Project Directory & Install Dependencies
```powershell
cd "d:\ai based water resource management"
pip install -r requirements.txt
```

### 4. Run Automated Test Suite
Ensure all 25 unit and integration tests pass:
```powershell
python -m pytest tests -v
```

### 5. Launch WaterGuard AI Dashboard
Start the application configured for port 8502 and local network accessibility:
```powershell
streamlit run app.py --server.port 8502 --server.address 0.0.0.0
```

When started, your terminal displays:
```text
  Local URL: http://localhost:8502
  Network URL: http://<your-local-network-IP>:8502
```
- **Local Access:** Open [http://localhost:8502](http://localhost:8502) on the same computer.
- **Local Network Access:** Open `http://<your-local-network-IP>:8502` from any phone, tablet, or laptop on the same local Wi-Fi / LAN.
- **Safe Server Shutdown:** Press `Ctrl + C` in the terminal to stop the application safely.

---

## 🎮 The 9 Simulation Scenarios

WaterGuard AI includes a built-in **Simulation Condition Controller** accessible directly from the Executive Dashboard. You can switch between any of the following 9 operational conditions in real time:

| # | Scenario Name | Affected Segment | Simulated Physical Condition | System Behavior & Diagnosis |
|---|---|---|---|---|
| **1** | **Normal Operation** | Network-wide | Nominal diurnal demand, stable pressure (2.5–6.0 bar), quiet acoustics (Index < 20). | Clean status, no active alerts, all segments scored low risk. |
| **2** | **Gradual Suspected Leakage** | `DN-204` (Heritage Cast Iron) | Unexplained flow deficit (~38 m³/h), localized pressure drop (-0.65 bar), elevated acoustic hiss (Index 62). | Generates **SUSPECTED_LEAK** alert with 88% confidence; elevates inspection score to 78. |
| **3** | **Sudden Burst-like Imbalance** | `TX-101` (Main Transmission) | Catastrophic trunk breach: -1.85 bar collapse, +320 m³/h surge, 88.0 acoustic cavitation, 6.2 mm/s vibration. | Generates **SUDDEN_BURST** CRITICAL alert; floors inspection priority at **Urgent Review (95/100)**; advises immediate valve isolation. |
| **4** | **Transient Pressure Anomaly** | `TX-102` (Feeder Main) | Rapid pressure surge (+1.40 bar) from valve cycling; mass-balance and acoustics remain normal. | Generates **PRESSURE_ANOMALY**; correctly avoids false leak diagnosis; prompts PRV inspection. |
| **5** | **Sensor Malfunction (Frozen / Unrealistic)** | `DN-201` (Metro East) | Pressure sensor stuck at 4.2 bar ($\sigma=0$ flatline) and flow meter reporting impossible negative value (-2.5 bar). | Sensor quality filter flags **SENSOR_FAULT**; marks segment **Insufficient Data**; dispatches instrument technician. |
| **6** | **Missing or Delayed Data** | `DN-203` (Industrial Loop) | Intermittent RTU gateway timeout; flow packets missing, pressure delayed by 2 hours. | Flags telemetry dropout; prompts communication gateway check. |
| **7** | **Increased Customer Demand** | `DN-201` (Residential) | Symmetrical flow surge (+180 m³/h inlet & outlet); natural Hazen-Williams friction drop (-0.22 bar); quiet acoustics. | **No false alert**; recognizes legitimate customer consumption pattern. |
| **8** | **Authorized Water Withdrawal** | `DN-203` (Industrial Park) | Scheduled hydrant testing (120 m³/h metered permit). | Discrepancy is fully reconciled by authorized permit tag ($W_{auth}$); **no leak alarm triggered**. |
| **9** | **Reservoir Storage Rebalance** | `TX-102` / `RES-NORTH` | Inflow exceeds outflow by +250 m³/h because water is filling the North Hill Reservoir. | Reconciled by positive storage change ($\Delta S$); **mass balance confirmed conserved**. |

---

## 🧠 Algorithmic Methodology

### 1. Multi-Indicator Leak & Anomaly Detection
WaterGuard AI **never** declares a pipeline leak based on a single sensor reading. An anomaly requires cross-modal corroboration:
1. **Sensor Quality Screening:** Verifies sensor readings are not frozen, missing, or outside physical PN16 bounds. Corrupted sensors generate instrument maintenance alerts rather than pipe leak alarms.
2. **Mass-Balance Conservation:** Calculates whether flow deficit exceeds composite meter uncertainty ($\pm 2\%$ tolerance).
3. **Hydraulic Gradient Analysis:** Compares measured pressure drop against theoretical friction loss calculated via empirical **Hazen-Williams equations**:
   $$h_f = 10.67 \cdot \frac{L}{C^{1.852} \cdot D^{4.8704}} \cdot Q^{1.852}$$
4. **Acoustic / Vibration Signature:** Checks for high-frequency acoustic hiss ($>50$ index) and turbulent vibration ($>3.0$ mm/s RMS) characteristic of pressurized orifice discharge.

### 2. Risk-to-Response Intelligence (0–100 Index)
The inspection priority score is calculated as:
$$\text{Priority Score} = \text{Immediate Telemetry Score (Max 55 pts)} + \text{Long-Term Asset Deterioration (Max 45 pts)}$$

- **Immediate Telemetry (55 pts):**
  - Active flow deficit / pressure drop: up to 35 pts
  - Acoustic / vibration cavitation: up to 20 pts
- **Long-Term Deterioration (45 pts):**
  - Material vulnerability & age: up to 20 pts *(Legacy Cast Iron & Concrete receive higher weight than modern HDPE)*
  - Historical repeat repair frequency: up to 15 pts
  - Supply consequence & nearby excavation risk: up to 10 pts

**Priority Tiers:**
- **Normal (0–29):** Standard annual preventative maintenance.
- **Monitor (30–59):** Track minimum night flows (02:00–04:00) and review cathodic protection.
- **Inspection Recommended (60–79):** Schedule non-destructive testing (CCTV/correlator) within 30 days.
- **Urgent Review (80–100):** Immediate field dispatch or physical isolation.
- **Insufficient Data:** Telemetry quality score $< 40\%$; hardware calibration required.

---

## 🧪 Automated Testing & Verification Results

The complete test suite is implemented in Python using `pytest`. All 25 tests execute deterministically without external hardware:

```powershell
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1
rootdir: D:\ai based water resource management
collected 25 items

tests/test_csv_handler.py::test_valid_assets_csv_parsing PASSED          [  4%]
tests/test_csv_handler.py::test_invalid_assets_csv_missing_columns PASSED [  8%]
tests/test_csv_handler.py::test_invalid_assets_csv_bad_data_types PASSED [ 12%]
tests/test_csv_handler.py::test_valid_readings_csv_parsing PASSED        [ 16%]
tests/test_csv_handler.py::test_invalid_readings_csv_bad_sensor_type PASSED [ 20%]
tests/test_database.py::test_database_initialization_and_seed PASSED     [ 24%]
tests/test_database.py::test_insert_and_query_sensor_readings PASSED     [ 28%]
tests/test_database.py::test_alert_lifecycle_persistence PASSED          [ 32%]
tests/test_database.py::test_maintenance_work_order_lifecycle PASSED     [ 36%]
tests/test_detection.py::test_normal_operation_no_alert PASSED           [ 40%]
tests/test_detection.py::test_gradual_leak_detected_with_multi_indicator PASSED [ 44%]
tests/test_detection.py::test_catastrophic_burst_detected PASSED         [ 48%]
tests/test_detection.py::test_sensor_malfunction_does_not_declare_pipe_leak PASSED [ 52%]
tests/test_risk_scoring.py::test_asset_vulnerability_score_calculation PASSED [ 56%]
tests/test_risk_scoring.py::test_composite_risk_evaluation_normal PASSED [ 60%]
tests/test_risk_scoring.py::test_composite_risk_evaluation_burst_urgent PASSED [ 64%]
tests/test_simulation.py::test_diurnal_multiplier_bounds PASSED          [ 68%]
tests/test_simulation.py::test_generate_segment_snapshot_healthy PASSED  [ 72%]
tests/test_simulation.py::test_sensor_fault_injection PASSED             [ 76%]
tests/test_simulation.py::test_scenario_manager_all_scenarios_exist PASSED [ 80%]
tests/test_water_balance.py::test_balanced_condition_within_tolerance PASSED [ 84%]
tests/test_water_balance.py::test_unexplained_leak_discrepancy_significant PASSED [ 88%]
tests/test_water_balance.py::test_authorized_withdrawal_reconciles_balance PASSED [ 92%]
tests/test_water_balance.py::test_reservoir_filling_storage_change_reconciles PASSED [ 96%]
tests/test_water_balance.py::test_system_summary_aggregation PASSED      [100%]

============================= 25 passed in 2.02s ==============================
```

---

## 🔮 Future ESP32 & Physical Hardware Integration Roadmap

WaterGuard AI was engineered from day one with cleanly abstracted interfaces to seamlessly integrate physical IoT sensor nodes without altering detection, risk scoring, or UI layers.

### Planned Hardware Topology:
```
[Piezoelectric Acoustic Transducer] ──┐
[4-20mA Industrial Pressure Sensor]  ├──> [ESP32-S3 IoT Node] ──(MQTT / LoRaWAN)──> [REST / Influx Ingestion API] ──> [WaterGuard AI]
[Electromagnetic Pulse Flow Meter]   ──┘
```

### Integration Interface Specification:
Physical ESP32 units will submit readings formatted in JSON matching the exact schema implemented in `models/sensor.py`:
```json
{
  "timestamp": "2026-10-24T08:15:00Z",
  "station_id": "MS-03",
  "segment_id": "TX-101",
  "sensor_type": "PRESSURE",
  "value": 5.82,
  "unit": "bar",
  "health_status": "HEALTHY",
  "is_synthetic": 0
}
```
Because the `SensorQualityFilter` and `AnomalyDetectionEngine` operate on standard dictionaries and pandas dataframes, physical hardware streams will feed directly into the SQLite `sensor_readings` table via standard POST endpoints.

---

## 📄 License & Attribution
Educational & Research Demonstration Prototype. Designed for smart water resource management studies and algorithmic pipeline integrity analysis.
