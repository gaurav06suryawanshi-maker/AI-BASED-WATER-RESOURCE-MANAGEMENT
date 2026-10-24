"""
Tests for water-balance calculations, mass conservation, and uncertainty propagation
"""
import pytest
from detection.water_balance import WaterBalanceCalculator


def test_balanced_condition_within_tolerance():
    # 1000 m3/h in, 990 m3/h out (1% difference within ±2% tolerance)
    res = WaterBalanceCalculator.calculate_balance(
        segment_id="TX-101",
        inflow_m3h=1000.0,
        outflow_m3h=990.0,
        storage_change_m3h=0.0,
        authorized_withdrawal_m3h=0.0,
    )
    assert res.unexplained_discrepancy_m3h == 10.0
    assert res.is_statistically_significant is False
    assert "Within Meter Tolerance" in res.status_label


def test_unexplained_leak_discrepancy_significant():
    # 1000 m3/h in, 880 m3/h out (120 m3/h loss, 12% discrepancy)
    res = WaterBalanceCalculator.calculate_balance(
        segment_id="TX-101",
        inflow_m3h=1000.0,
        outflow_m3h=880.0,
        storage_change_m3h=0.0,
        authorized_withdrawal_m3h=0.0,
    )
    assert res.unexplained_discrepancy_m3h == 120.0
    assert res.is_statistically_significant is True
    assert res.uncertainty_band_m3h < 120.0  # Discrepancy exceeds uncertainty
    assert "Deficit" in res.status_label or "Discrepancy" in res.status_label


def test_authorized_withdrawal_reconciles_balance():
    # Inflow 1000, Outflow 880, but Authorized permit is 120 m3/h
    res = WaterBalanceCalculator.calculate_balance(
        segment_id="DN-203",
        inflow_m3h=1000.0,
        outflow_m3h=880.0,
        storage_change_m3h=0.0,
        authorized_withdrawal_m3h=120.0,
    )
    # Reconciled discrepancy should be 0.0
    assert res.unexplained_discrepancy_m3h == 0.0
    assert res.is_statistically_significant is False


def test_reservoir_filling_storage_change_reconciles():
    # Inflow 1000, Outflow 750, Tank storing +250 m3/h
    res = WaterBalanceCalculator.calculate_balance(
        segment_id="TX-102",
        inflow_m3h=1000.0,
        outflow_m3h=750.0,
        storage_change_m3h=250.0,
        authorized_withdrawal_m3h=0.0,
    )
    assert res.unexplained_discrepancy_m3h == 0.0
    assert res.is_statistically_significant is False


def test_system_summary_aggregation():
    res1 = WaterBalanceCalculator.calculate_balance("SEG-1", 1000.0, 995.0)
    res2 = WaterBalanceCalculator.calculate_balance("SEG-2", 500.0, 420.0)  # 80 loss
    summary = WaterBalanceCalculator.calculate_system_summary([res1, res2])

    assert summary["total_inflow_m3h"] == 1500.0
    assert summary["total_outflow_m3h"] == 1415.0
    assert summary["total_unexplained_discrepancy_m3h"] == 85.0
    assert "SEG-2" in summary["segments_with_discrepancy"]
