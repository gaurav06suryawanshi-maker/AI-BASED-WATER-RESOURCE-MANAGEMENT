"""
Simulation Scenarios Manager
Defines all nine required simulation conditions:
1. Normal Operation
2. Gradual Suspected Leakage
3. Sudden Burst-like Flow Imbalance
4. Pressure Anomaly (Surge/Hammer)
5. Sensor Malfunction (Frozen/Unrealistic)
6. Missing or Delayed Data
7. Increased Legitimate Demand
8. Authorized Water Withdrawal
9. Reservoir Storage Change
"""
from enum import Enum
from typing import Dict, Any, List, Optional
from models.sensor import SensorHealthStatus


class ScenarioType(str, Enum):
    NORMAL = "NORMAL_OPERATION"
    GRADUAL_LEAK = "GRADUAL_SUSPECTED_LEAK"
    SUDDEN_BURST = "SUDDEN_BURST_IMBALANCE"
    PRESSURE_ANOMALY = "PRESSURE_ANOMALY_SURGE"
    SENSOR_MALFUNCTION = "SENSOR_MALFUNCTION"
    MISSING_DELAYED = "MISSING_DELAYED_DATA"
    INCREASED_DEMAND = "INCREASED_LEGITIMATE_DEMAND"
    AUTHORIZED_WITHDRAWAL = "AUTHORIZED_WATER_WITHDRAWAL"
    RESERVOIR_CHANGE = "RESERVOIR_STORAGE_CHANGE"


class SimulationScenarioManager:
    """Configures parameter overrides and hydraulic offsets for reproducible test scenarios."""

    SCENARIO_CONFIGS: Dict[str, Dict[str, Any]] = {
        ScenarioType.NORMAL.value: {
            "name": "1. Normal Operation",
            "description": "Baseline nominal condition. Standard diurnal flow cycles, stable pressure, quiet acoustics, healthy telemetry.",
            "target_segment": None,
            "overrides": {},
            "authorized_withdrawals_m3h": {},
            "expected_alert": None,
        },
        ScenarioType.GRADUAL_LEAK.value: {
            "name": "2. Gradual Suspected Leakage",
            "description": "Slowly developing fracture on DN-204 (Old Quarter Heritage Cast Iron). Flow discrepancy of ~38 m³/h, pressure dip of ~0.65 bar, elevated acoustic hiss (index 62.0).",
            "target_segment": "DN-204",
            "overrides": {
                "DN-204": {
                    "flow_offset": 38.0,            # Inflow increases to supply leak + baseline
                    "pressure_offset": -0.65,       # Localized pressure drop due to hydraulic head loss
                    "acoustic_offset": 45.0,        # Continuous pipe wall acoustic vibration
                    "vibration_offset": 2.2,
                    "pressure_notes": "Hydraulic pressure depressed below local hydraulic gradient",
                    "flow_notes": "Unaccounted outflow discrepancy detected",
                    "acoustic_notes": "Elevated acoustic signature characteristic of pressurized orifice spray",
                }
            },
            "authorized_withdrawals_m3h": {},
            "expected_alert": "SUSPECTED_LEAK",
        },
        ScenarioType.SUDDEN_BURST.value: {
            "name": "3. Sudden Burst-like Flow Imbalance",
            "description": "Catastrophic main transmission breach on TX-101. Major pressure collapse (-1.85 bar), severe inflow surge (+320 m³/h), violent vibration (6.2 mm/s), high acoustic alarm (88.0).",
            "target_segment": "TX-101",
            "overrides": {
                "TX-101": {
                    "flow_offset": 320.0,
                    "pressure_offset": -1.85,
                    "acoustic_offset": 70.0,
                    "vibration_offset": 4.8,
                    "pressure_notes": "Sharp step-down in trunk line pressure",
                    "flow_notes": "Severe instantaneous mass-balance rupture",
                    "acoustic_notes": "High amplitude cavitation and pipe wall turbulence",
                }
            },
            "authorized_withdrawals_m3h": {},
            "expected_alert": "SUDDEN_BURST",
        },
        ScenarioType.PRESSURE_ANOMALY.value: {
            "name": "4. Transient Pressure Anomaly (Surge / Hammer)",
            "description": "Rapid valve cycling or booster trip on TX-102. High pressure spike (+1.4 bar) without corresponding volumetric water loss. Normal acoustic baseline.",
            "target_segment": "TX-102",
            "overrides": {
                "TX-102": {
                    "flow_offset": 0.0,
                    "pressure_offset": 1.40,
                    "acoustic_offset": 0.0,
                    "vibration_offset": 0.2,
                    "pressure_notes": "Pressure transient spike exceeding normal regulation bounds",
                }
            },
            "authorized_withdrawals_m3h": {},
            "expected_alert": "PRESSURE_ANOMALY",
        },
        ScenarioType.SENSOR_MALFUNCTION.value: {
            "name": "5. Sensor Malfunction (Frozen / Unrealistic)",
            "description": "Transducer telemetry fault on MS-06 (DN-201). Pressure sensor output frozen flatline without natural noise, and flow meter reporting impossible physical values (-2.5 / 9999).",
            "target_segment": "DN-201",
            "overrides": {
                "DN-201": {
                    "pressure_health": SensorHealthStatus.FROZEN.value,
                    "flow_health": SensorHealthStatus.UNREALISTIC.value,
                    "pressure_notes": "ADC stalled: 0.0 standard deviation over consecutive frames",
                    "flow_notes": "Reading violates physical limits of DN-201 pipeline cross-section",
                }
            },
            "authorized_withdrawals_m3h": {},
            "expected_alert": "SENSOR_FAULT",
        },
        ScenarioType.MISSING_DELAYED.value: {
            "name": "6. Missing or Delayed Data",
            "description": "Cellular gateway intermittent outage on MS-08 (DN-203). Flow and acoustic packets dropped (Missing), pressure packets delayed by 2 hours.",
            "target_segment": "DN-203",
            "overrides": {
                "DN-203": {
                    "flow_health": SensorHealthStatus.MISSING.value,
                    "acoustic_health": SensorHealthStatus.MISSING.value,
                    "pressure_health": SensorHealthStatus.DELAYED.value,
                    "flow_notes": "Telemetry packet timed out",
                    "pressure_notes": "Out-of-sequence timestamp received",
                }
            },
            "authorized_withdrawals_m3h": {},
            "expected_alert": "SENSOR_FAULT",
        },
        ScenarioType.INCREASED_DEMAND.value: {
            "name": "7. Increased Legitimate Customer Demand",
            "description": "Simultaneous demand surge in residential feeder DN-201 (+180 m³/h). Both upstream and downstream flow rise symmetrically. Pressure experiences normal hydraulic head drop, acoustics quiet.",
            "target_segment": "DN-201",
            "overrides": {
                "DN-201": {
                    "flow_offset": 180.0,
                    "pressure_offset": -0.22,  # Natural Hazen-Williams friction drop
                    "acoustic_offset": 2.0,    # Normal laminar/turbulent noise increase
                    "vibration_offset": 0.1,
                    "flow_notes": "Symmetrical flow increase across inlet and outlet",
                }
            },
            "authorized_withdrawals_m3h": {},
            "expected_alert": None,  # Not an anomaly
        },
        ScenarioType.AUTHORIZED_WITHDRAWAL.value: {
            "name": "8. Authorized Water Withdrawal",
            "description": "Scheduled municipal hydrant testing and industrial supply intake on DN-203 (120 m³/h metered permit). Mass-balance discrepancy is fully reconciled by authorized permit.",
            "target_segment": "DN-203",
            "overrides": {
                "DN-203": {
                    "flow_offset": 120.0,
                    "pressure_offset": -0.30,
                    "acoustic_offset": 8.0,
                    "flow_notes": "Permitted temporary withdrawal active",
                }
            },
            "authorized_withdrawals_m3h": {
                "DN-203": 120.0,
            },
            "expected_alert": None,  # Reconciled withdrawal
        },
        ScenarioType.RESERVOIR_CHANGE.value: {
            "name": "9. Reservoir Storage Rebalance",
            "description": "Scheduled off-peak refilling of North Hill Reservoir RES-NORTH via feeder TX-102. Transmission inflow increases by 250 m³/h while downstream distribution remains constant, balancing the storage delta.",
            "target_segment": "TX-102",
            "overrides": {
                "TX-102": {
                    "flow_offset": 250.0,
                    "pressure_offset": -0.15,
                    "acoustic_offset": 3.0,
                    "flow_notes": "Inflow routed to storage filling",
                }
            },
            "authorized_withdrawals_m3h": {},
            "reservoir_storage_delta_m3h": {
                "RES-NORTH": 250.0,
            },
            "expected_alert": None,  # Balanced by Delta S
        },
    }

    @classmethod
    def get_all_scenarios(cls) -> Dict[str, Dict[str, Any]]:
        return cls.SCENARIO_CONFIGS

    @classmethod
    def get_scenario(cls, scenario_key: str) -> Dict[str, Any]:
        return cls.SCENARIO_CONFIGS.get(scenario_key, cls.SCENARIO_CONFIGS[ScenarioType.NORMAL.value])
