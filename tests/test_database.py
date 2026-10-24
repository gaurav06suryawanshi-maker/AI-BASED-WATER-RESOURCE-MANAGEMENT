"""
Tests for SQLite persistence, CRUD operations, and incident tracking
"""
import pytest
import tempfile
from pathlib import Path
from database.db import DatabaseManager
from models.alert import AlertCategory, AlertSeverity, IncidentStatus


@pytest.fixture
def temp_db():
    import gc
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        temp_path = Path(tf.name)
    db = DatabaseManager(db_path=temp_path)
    yield db
    del db
    gc.collect()
    try:
        if temp_path.exists():
            temp_path.unlink()
    except OSError:
        pass


def test_database_initialization_and_seed(temp_db):
    segments = temp_db.get_all_segments()
    assert len(segments) >= 8
    stations = temp_db.get_all_stations()
    assert len(stations) >= 9
    reservoirs = temp_db.get_all_reservoirs()
    assert len(reservoirs) >= 2


def test_insert_and_query_sensor_readings(temp_db):
    readings = [
        {
            "timestamp": "2026-10-24 10:00:00",
            "station_id": "MS-01",
            "segment_id": "TX-100",
            "sensor_type": "PRESSURE",
            "value": 4.5,
            "unit": "bar",
            "health_status": "HEALTHY",
            "is_synthetic": 1,
            "flag_notes": None,
        }
    ]
    temp_db.insert_sensor_readings(readings)
    history = temp_db.get_telemetry_history(segment_id="TX-100", limit=10)
    assert len(history) == 1
    assert history[0]["value"] == 4.5


def test_alert_lifecycle_persistence(temp_db):
    alert_data = {
        "timestamp": "2026-10-24 10:00:00",
        "segment_id": "TX-101",
        "category": AlertCategory.SUSPECTED_LEAK.value,
        "severity": AlertSeverity.HIGH.value,
        "title": "Suspected Subsurface Leak",
        "description": "Flow discrepancy of 42 m3/h",
        "evidence_data": "{}",
        "confidence_pct": 88.0,
        "confidence_explanation": "Corroborated by acoustic signature",
        "required_checks": "Deploy acoustic mic",
        "recommended_action": "Verify meter",
        "status": IncidentStatus.ACTIVE.value,
        "review_notes": None,
        "assigned_technician": None,
        "resolved_at": None,
    }
    alert_id = temp_db.insert_alert(alert_data)
    assert alert_id is not None

    alerts = temp_db.get_alerts(status="ACTIVE")
    assert any(a["alert_id"] == alert_id for a in alerts)

    # Acknowledge
    temp_db.update_alert_status(alert_id, status="ACKNOWLEDGED", notes="Reviewed by dispatch", technician="Unit 4")
    updated = temp_db.get_alerts(status="ACKNOWLEDGED")
    target = next(a for a in updated if a["alert_id"] == alert_id)
    assert target["status"] == "ACKNOWLEDGED"
    assert target["assigned_technician"] == "Unit 4"

    # Resolve
    temp_db.update_alert_status(alert_id, status="RESOLVED", notes="Repaired leak clamp")
    resolved = temp_db.get_alerts(status="RESOLVED")
    assert any(a["alert_id"] == alert_id for a in resolved)


def test_maintenance_work_order_lifecycle(temp_db):
    rec_data = {
        "segment_id": "TX-102",
        "priority_score": 68.5,
        "priority_category": "Inspection Recommended",
        "estimated_condition": "Grade 4 - Poor",
        "contributing_reasons": "Age and soil corrosion",
        "recommended_action": "Schedule CCTV inspection",
        "status": "Pending",
        "assigned_to": "Field Team 2",
        "scheduled_date": "2026-11-20",
        "notes": "Initial priority assignment",
    }
    rec_id = temp_db.save_maintenance_record(rec_data)
    assert rec_id is not None

    records = temp_db.get_maintenance_records(segment_id="TX-102")
    assert len(records) >= 1
    assert records[0]["status"] == "Pending"

    # Update status to Scheduled
    temp_db.update_maintenance_status(rec_id, status="Scheduled", notes="Contractor assigned")
    updated = temp_db.get_maintenance_records(segment_id="TX-102")
    assert updated[0]["status"] == "Scheduled"
