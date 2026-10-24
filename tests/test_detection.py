"""
Tests for multi-indicator leak and anomaly detection engine
"""
import pytest
from datetime import datetime
from detection.engine import AnomalyDetectionEngine
from detection.quality_filter import SensorQualityFilter
from models.sensor import SensorType, SensorHealthStatus
from models.alert import AlertCategory, AlertSeverity


@pytest.fixture
def test_segment():
    return {
        "segment_id": "TEST-101",
        "name": "Test Transmission Line",
        "upstream_station_id": "MS-01",
        "downstream_station_id": "MS-02",
        "length_km": 5.0,
        "diameter_mm": 800,
        "material": "Ductile Iron",
        "installation_year": 2010,
        "nominal_pressure_bar": 5.0,
        "nominal_flow_m3h": 1000.0,
        "criticality": "High",
    }


def test_normal_operation_no_alert(test_segment):
    engine = AnomalyDetectionEngine()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    readings = {
        SensorType.PRESSURE.value: {"value": 5.02, "unit": "bar", "health_status": "HEALTHY", "sensor_type": "PRESSURE"},
        SensorType.FLOW.value: {"value": 998.0, "unit": "m³/h", "health_status": "HEALTHY", "sensor_type": "FLOW"},
        SensorType.ACOUSTIC.value: {"value": 15.0, "unit": "Index (0-100)", "health_status": "HEALTHY", "sensor_type": "ACOUSTIC"},
        SensorType.VIBRATION.value: {"value": 1.0, "unit": "mm/s", "health_status": "HEALTHY", "sensor_type": "VIBRATION"},
    }

    alert, ctx = engine.evaluate_segment(test_segment, readings, downstream_flow_m3h=995.0)
    assert alert is None
    assert ctx["diagnosis"] == "NORMAL"


def test_gradual_leak_detected_with_multi_indicator(test_segment):
    engine = AnomalyDetectionEngine()
    # Flow loss (1040 in vs 960 out = 80 deficit), Pressure depressed to 4.3 bar (-0.7 bar), Acoustic elevated to 65
    readings = {
        SensorType.PRESSURE.value: {"value": 4.30, "unit": "bar", "health_status": "HEALTHY", "sensor_type": "PRESSURE"},
        SensorType.FLOW.value: {"value": 1040.0, "unit": "m³/h", "health_status": "HEALTHY", "sensor_type": "FLOW"},
        SensorType.ACOUSTIC.value: {"value": 65.0, "unit": "Index (0-100)", "health_status": "HEALTHY", "sensor_type": "ACOUSTIC"},
        SensorType.VIBRATION.value: {"value": 2.8, "unit": "mm/s", "health_status": "HEALTHY", "sensor_type": "VIBRATION"},
    }

    alert, ctx = engine.evaluate_segment(test_segment, readings, downstream_flow_m3h=960.0)
    assert alert is not None
    assert alert.category == AlertCategory.SUSPECTED_LEAK.value
    assert alert.severity == AlertSeverity.HIGH.value
    assert alert.confidence_pct >= 80.0
    assert "Suspected Subsurface Pipe Leakage" in alert.title


def test_catastrophic_burst_detected(test_segment):
    engine = AnomalyDetectionEngine()
    # Sudden pressure collapse to 3.1 bar (-1.9 bar), flow surge 1350 vs 700 downstream, acoustic 88.0
    readings = {
        SensorType.PRESSURE.value: {"value": 3.10, "unit": "bar", "health_status": "HEALTHY", "sensor_type": "PRESSURE"},
        SensorType.FLOW.value: {"value": 1350.0, "unit": "m³/h", "health_status": "HEALTHY", "sensor_type": "FLOW"},
        SensorType.ACOUSTIC.value: {"value": 88.0, "unit": "Index (0-100)", "health_status": "HEALTHY", "sensor_type": "ACOUSTIC"},
        SensorType.VIBRATION.value: {"value": 5.5, "unit": "mm/s", "health_status": "HEALTHY", "sensor_type": "VIBRATION"},
    }

    alert, ctx = engine.evaluate_segment(test_segment, readings, downstream_flow_m3h=700.0)
    assert alert is not None
    assert alert.category == AlertCategory.SUDDEN_BURST.value
    assert alert.severity == AlertSeverity.CRITICAL.value
    assert "Burst" in alert.title


def test_sensor_malfunction_does_not_declare_pipe_leak(test_segment):
    engine = AnomalyDetectionEngine()
    # Sensor reports frozen value or physically impossible value
    readings = {
        SensorType.PRESSURE.value: {"value": -2.5, "unit": "bar", "health_status": "UNREALISTIC", "sensor_type": "PRESSURE"},
        SensorType.FLOW.value: {"value": 1000.0, "unit": "m³/h", "health_status": "HEALTHY", "sensor_type": "FLOW"},
        SensorType.ACOUSTIC.value: {"value": 15.0, "unit": "Index (0-100)", "health_status": "HEALTHY", "sensor_type": "ACOUSTIC"},
    }

    alert, ctx = engine.evaluate_segment(test_segment, readings)
    assert alert is not None
    # Must be categorized as SENSOR_FAULT, NOT a leak!
    assert alert.category == AlertCategory.SENSOR_FAULT.value
    assert alert.category != AlertCategory.SUSPECTED_LEAK.value
    assert ctx["diagnosis"] == "SENSOR_FAULT"
