"""
Tests for explainable risk-to-response scoring and prioritization logic
"""
import pytest
from risk.scoring import RiskScoringEngine
from risk.recommendations import RecommendationGenerator


def test_asset_vulnerability_score_calculation():
    # Old Cast Iron segment installed 1978 (age ~48), 5 past repairs, Corrosive soil, Critical
    seg = {
        "segment_id": "DN-204",
        "name": "Heritage Reticulation",
        "material": "Cast Iron",
        "installation_year": 1978,
        "past_repair_count": 5,
        "criticality": "Critical",
        "soil_condition": "Corrosive",
        "nearby_excavation_risk": 1,
    }
    score, breakdown, reasons = RiskScoringEngine.calculate_asset_vulnerability_score(seg)
    assert score >= 40.0  # High long-term asset risk
    assert breakdown["asset_age_material"] == 20.0
    assert breakdown["incident_history"] == 15.0
    assert breakdown["criticality_consequence"] == 10.0
    assert len(reasons) >= 3


def test_composite_risk_evaluation_normal():
    # Modern HDPE installed 2020, 0 repairs, low criticality
    seg = {
        "segment_id": "DN-NEW",
        "name": "New Distribution Feeder",
        "material": "HDPE",
        "installation_year": 2020,
        "past_repair_count": 0,
        "criticality": "Low",
        "nominal_pressure_bar": 3.5,
        "nominal_flow_m3h": 400.0,
    }
    res = RiskScoringEngine.evaluate_segment_risk(seg, detection_context={"diagnosis": "NORMAL"})
    assert res.priority_score < 30.0
    assert res.priority_category == "NORMAL"
    assert "Grade 1" in res.estimated_condition_grade or "Grade 2" in res.estimated_condition_grade


def test_composite_risk_evaluation_burst_urgent():
    seg = {
        "segment_id": "TX-101",
        "name": "Main Transmission Trunk",
        "material": "Ductile Iron",
        "installation_year": 2005,
        "past_repair_count": 1,
        "criticality": "Critical",
        "nominal_pressure_bar": 5.8,
        "nominal_flow_m3h": 2400.0,
    }
    burst_context = {
        "diagnosis": "SUDDEN_BURST",
        "hydraulic": None,
        "water_balance": None,
        "acoustic": None,
    }
    res = RiskScoringEngine.evaluate_segment_risk(seg, detection_context=burst_context)
    assert res.priority_score >= 80.0
    assert res.priority_category == "URGENT_REVIEW"
    assert "Immediate physical isolation" in res.recommended_response
