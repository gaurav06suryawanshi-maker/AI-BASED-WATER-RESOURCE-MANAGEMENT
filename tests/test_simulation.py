"""
Tests for physics-inspired sensor simulation and scenario generation
"""
import pytest
from datetime import datetime
from simulation.sensor_simulator import SensorSimulator
from simulation.scenarios import SimulationScenarioManager, ScenarioType
from models.sensor import SensorType, SensorHealthStatus


def test_diurnal_multiplier_bounds():
    sim = SensorSimulator(random_seed=42)
    # Check diurnal curve across 24 hours
    for h in range(24):
        dt = datetime(2026, 10, 24, h, 0, 0)
        mult = sim.get_diurnal_multiplier(dt)
        assert 0.45 <= mult <= 1.50
    # Check that morning peak (08:00) is higher than night dip (03:00)
    morning = sim.get_diurnal_multiplier(datetime(2026, 10, 24, 8, 0, 0))
    night = sim.get_diurnal_multiplier(datetime(2026, 10, 24, 3, 0, 0))
    assert morning > night


def test_generate_segment_snapshot_healthy():
    sim = SensorSimulator(random_seed=42)
    dt = datetime(2026, 10, 24, 12, 0, 0)
    mock_seg = {
        "segment_id": "TEST-01",
        "name": "Test Segment",
        "upstream_station_id": "MS-01",
        "downstream_station_id": "MS-02",
        "nominal_pressure_bar": 5.0,
        "nominal_flow_m3h": 1000.0,
    }
    readings = sim.generate_segment_snapshot(dt, mock_seg)
    assert len(readings) == 4

    types = {r.sensor_type for r in readings}
    assert types == {SensorType.PRESSURE.value, SensorType.FLOW.value, SensorType.ACOUSTIC.value, SensorType.VIBRATION.value}

    for r in readings:
        assert r.health_status == SensorHealthStatus.HEALTHY.value
        assert r.is_synthetic is True
        assert r.value is not None
        assert r.value > 0.0


def test_sensor_fault_injection():
    sim = SensorSimulator(random_seed=42)
    dt = datetime(2026, 10, 24, 12, 0, 0)
    mock_seg = {
        "segment_id": "TEST-01",
        "name": "Test Segment",
        "upstream_station_id": "MS-01",
        "downstream_station_id": "MS-02",
        "nominal_pressure_bar": 5.0,
        "nominal_flow_m3h": 1000.0,
    }
    overrides = {
        "TEST-01": {
            "pressure_health": SensorHealthStatus.FROZEN.value,
            "flow_health": SensorHealthStatus.MISSING.value,
            "acoustic_health": SensorHealthStatus.UNREALISTIC.value,
        }
    }
    readings = sim.generate_segment_snapshot(dt, mock_seg, overrides)
    reading_dict = {r.sensor_type: r for r in readings}

    # Frozen
    assert reading_dict[SensorType.PRESSURE.value].health_status == SensorHealthStatus.FROZEN.value
    # Missing
    assert reading_dict[SensorType.FLOW.value].health_status == SensorHealthStatus.MISSING.value
    assert reading_dict[SensorType.FLOW.value].value is None
    # Unrealistic
    assert reading_dict[SensorType.ACOUSTIC.value].health_status == SensorHealthStatus.UNREALISTIC.value


def test_scenario_manager_all_scenarios_exist():
    scenarios = SimulationScenarioManager.get_all_scenarios()
    assert len(scenarios) == 9
    assert ScenarioType.NORMAL.value in scenarios
    assert ScenarioType.GRADUAL_LEAK.value in scenarios
    assert ScenarioType.SUDDEN_BURST.value in scenarios
    assert ScenarioType.SENSOR_MALFUNCTION.value in scenarios
