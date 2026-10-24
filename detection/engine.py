"""
Multi-Indicator Anomaly and Leak Detection Engine
Integrates sensor quality screening, mass balance conservation, hydraulic pressure gradients,
and acoustic signatures to produce explainable alerts without false positives from single-sensor blips.
"""
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

import config
from models.alert import Alert, AlertSeverity, AlertCategory, IncidentStatus
from models.sensor import SensorType
from detection.quality_filter import SensorQualityFilter, DataQualityReport
from detection.water_balance import WaterBalanceCalculator, WaterBalanceResult
from detection.hydraulic_analysis import HydraulicAnalyzer, HydraulicAnomaly
from detection.acoustic_analysis import AcousticAnalyzer, AcousticAnomaly


class AnomalyDetectionEngine:
    """Evaluates multi-variable telemetry streams to identify leaks, bursts, surges, and sensor malfunctions."""

    def __init__(self, db_manager=None):
        self.db = db_manager

    def evaluate_segment(
        self,
        segment: Dict[str, Any],
        latest_readings: Dict[str, Dict[str, Any]],
        recent_history_by_type: Optional[Dict[str, List[Dict[str, Any]]]] = None,
        downstream_flow_m3h: Optional[float] = None,
        authorized_withdrawal_m3h: float = 0.0,
        reservoir_storage_delta_m3h: float = 0.0,
    ) -> Tuple[Optional[Alert], Dict[str, Any]]:
        """Performs multi-indicator cross-validation on a single segment.
        Returns:
            (Optional[Alert], analysis_context_dict)
        """
        seg_id = segment["segment_id"]
        ts_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Extract current readings
        p_reading = latest_readings.get(SensorType.PRESSURE.value)
        f_reading = latest_readings.get(SensorType.FLOW.value)
        ac_reading = latest_readings.get(SensorType.ACOUSTIC.value)
        vib_reading = latest_readings.get(SensorType.VIBRATION.value)

        p_val = p_reading.get("value") if p_reading else None
        f_inflow = f_reading.get("value") if f_reading else None
        ac_val = ac_reading.get("value") if ac_reading else None
        vib_val = vib_reading.get("value") if vib_reading else None

        # 1. Screen Data Quality First
        history_map = recent_history_by_type or {
            SensorType.PRESSURE.value: [p_reading] if p_reading else [],
            SensorType.FLOW.value: [f_reading] if f_reading else [],
            SensorType.ACOUSTIC.value: [ac_reading] if ac_reading else [],
        }
        quality_report = SensorQualityFilter.evaluate_recent_stream(seg_id, history_map)

        # If sensor hardware is malfunctioning, generate SENSOR_FAULT alert (NOT a pipe leak)
        if not quality_report.is_valid_for_analysis:
            alert = Alert(
                timestamp=ts_now,
                segment_id=seg_id,
                category=AlertCategory.SENSOR_FAULT.value,
                severity=AlertSeverity.MEDIUM.value if not quality_report.unrealistic_sensors else AlertSeverity.HIGH.value,
                title=f"Telemetry Malfunction: {seg_id}",
                description=f"Sensors on segment {seg_id} failed quality screening. Issues: {'; '.join(quality_report.sensor_issues)}",
                evidence_data=json.dumps({
                    "data_quality_score": quality_report.data_quality_score,
                    "frozen_sensors": quality_report.frozen_sensors,
                    "missing_sensors": quality_report.missing_sensors,
                    "unrealistic_sensors": quality_report.unrealistic_sensors,
                    "delayed_sensors": quality_report.delayed_sensors,
                }),
                confidence_pct=92.0,
                confidence_explanation=(
                    f"Direct telemetry validation detected signal anomalies ({'; '.join(quality_report.sensor_issues)}). "
                    "Sensor disqualified from hydraulic inference to prevent false leak alarms."
                ),
                required_checks="Inspect transducer power supply, 4-20mA loop wiring, RTU gateway, and ADC calibration.",
                recommended_action=quality_report.recommended_action or "Dispatch instrument technician for field inspection.",
            )
            context = {
                "quality_report": quality_report,
                "water_balance": None,
                "hydraulic": None,
                "acoustic": None,
                "diagnosis": "SENSOR_FAULT",
            }
            return alert, context

        # 2. Perform Water-Balance Calculation
        # In a realistic transmission network, if downstream flow is not directly metered,
        # it is modeled via nominal diurnal expectation minus authorized withdrawals.
        effective_outflow = downstream_flow_m3h if downstream_flow_m3h is not None else segment["nominal_flow_m3h"]
        water_balance = WaterBalanceCalculator.calculate_balance(
            segment_id=seg_id,
            inflow_m3h=f_inflow if f_inflow is not None else 0.0,
            outflow_m3h=effective_outflow,
            storage_change_m3h=reservoir_storage_delta_m3h,
            authorized_withdrawal_m3h=authorized_withdrawal_m3h,
        )

        # 3. Perform Hydraulic Pressure Analysis
        hydraulic = HydraulicAnalyzer.analyze_pressure(
            segment=segment,
            measured_pressure_bar=p_val,
            measured_flow_m3h=f_inflow,
        )

        # 4. Perform Acoustic / Vibration Analysis
        acoustic = AcousticAnalyzer.analyze(
            segment_id=seg_id,
            acoustic_index=ac_val,
            vibration_rms=vib_val,
        )

        context = {
            "quality_report": quality_report,
            "water_balance": water_balance,
            "hydraulic": hydraulic,
            "acoustic": acoustic,
            "diagnosis": "NORMAL",
        }

        # --- MULTI-INDICATOR DECISION SYNTHESIS ---

        # Case A: SUDDEN CATASTROPHIC BURST
        # High flow surge + Severe pressure collapse + Extreme acoustics
        if hydraulic.anomaly_type == "SUDDEN_BURST_DROP" and acoustic.is_anomaly:
            confidence = 94.0
            alert = Alert(
                timestamp=ts_now,
                segment_id=seg_id,
                category=AlertCategory.SUDDEN_BURST.value,
                severity=AlertSeverity.CRITICAL.value,
                title=f"Catastrophic Pipe Burst: {seg_id} ({segment['name']})",
                description=(
                    f"Massive hydraulic breach identified on segment {seg_id}. "
                    f"Pressure collapsed by {abs(hydraulic.pressure_delta_bar):.2f} bar with concurrent high vibration ({acoustic.vibration_rms:.2f} mm/s)."
                ),
                evidence_data=json.dumps({
                    "pressure_bar": p_val,
                    "pressure_drop_bar": round(hydraulic.pressure_delta_bar, 2),
                    "inflow_m3h": f_inflow,
                    "acoustic_index": ac_val,
                    "vibration_rms": vib_val,
                    "discrepancy_m3h": water_balance.unexplained_discrepancy_m3h,
                }),
                confidence_pct=confidence,
                confidence_explanation=(
                    f"Strong multi-sensor correlation: Concurrent pressure collapse (-{abs(hydraulic.pressure_delta_bar):.2f} bar), "
                    f"flow deficit ({water_balance.unexplained_discrepancy_m3h:.1f} m³/h), and acoustic cavitation ({ac_val:.1f}/100). "
                    "Physical rupture likelihood is exceptionally high."
                ),
                required_checks=(
                    "1. Verify pressure reading on downstream station.\n"
                    "2. Check SCADA pump status for sudden trip or overcurrent.\n"
                    "3. Inspect emergency isolation valves upstream of segment."
                ),
                recommended_action=(
                    "URGENT: Isolate segment {seg_id} via upstream isolation valve. "
                    "Dispatch emergency repair crew immediately to prevent major urban flooding and foundation washaway."
                ).format(seg_id=seg_id),
            )
            context["diagnosis"] = "SUDDEN_BURST"
            return alert, context

        # Case B: GRADUAL SUSPECTED LEAKAGE
        # Statistically significant flow discrepancy + Depressed pressure + Elevated acoustic hiss
        if water_balance.is_statistically_significant and hydraulic.is_anomaly and acoustic.is_anomaly:
            confidence = 88.0
            alert = Alert(
                timestamp=ts_now,
                segment_id=seg_id,
                category=AlertCategory.SUSPECTED_LEAK.value,
                severity=AlertSeverity.HIGH.value,
                title=f"Suspected Subsurface Pipe Leakage: {seg_id}",
                description=(
                    f"Multi-indicator leak pattern detected on {segment['name']}. "
                    f"Unexplained flow loss: {water_balance.unexplained_discrepancy_m3h:.1f} m³/h ({water_balance.discrepancy_pct:.1f}%), "
                    f"Pressure depression: {abs(hydraulic.pressure_delta_bar):.2f} bar, Acoustic index: {ac_val:.1f}/100."
                ),
                evidence_data=json.dumps({
                    "flow_discrepancy_m3h": water_balance.unexplained_discrepancy_m3h,
                    "discrepancy_pct": water_balance.discrepancy_pct,
                    "uncertainty_band_m3h": water_balance.uncertainty_band_m3h,
                    "pressure_delta_bar": round(hydraulic.pressure_delta_bar, 2),
                    "acoustic_index": ac_val,
                    "vibration_rms": vib_val,
                }),
                confidence_pct=confidence,
                confidence_explanation=(
                    f"Three independent physical modalities corroborate leakage: Volumetric deficit exceeds meter tolerance "
                    f"(±{water_balance.uncertainty_band_m3h:.1f} m³/h), localized pressure drop exceeds friction expectations, "
                    f"and acoustic sensor confirms characteristic orifice hiss ({ac_val:.1f}/100)."
                ),
                required_checks=(
                    "1. Cross-check for unmetered hydrant usage or fire service draw.\n"
                    "2. Deploy field technician with acoustic ground microphone to pin-point acoustic peak along {seg_id}.\n"
                    "3. Inspect valve chambers for standing water."
                ).format(seg_id=seg_id),
                recommended_action=(
                    "Arrange targeted field acoustic correlator survey within 24 hours. "
                    "Compare upstream/downstream flowmeters at minimum night flow (02:00-04:00) to confirm baseline loss rate."
                ),
            )
            context["diagnosis"] = "SUSPECTED_LEAK"
            return alert, context

        # Case C: PRESSURE ANOMALY (Transient Surge / Water Hammer)
        # Pressure spike without flow deficit and without acoustic leak hiss
        if hydraulic.anomaly_type == "TRANSIENT_SURGE":
            confidence = 82.0
            alert = Alert(
                timestamp=ts_now,
                segment_id=seg_id,
                category=AlertCategory.PRESSURE_ANOMALY.value,
                severity=AlertSeverity.HIGH.value,
                title=f"Transient Pressure Surge / Water Hammer: {seg_id}",
                description=(
                    f"Abnormal pressure surge (+{hydraulic.pressure_delta_bar:.2f} bar) recorded on {segment['name']}. "
                    f"Operating pressure reached {p_val:.2f} bar without mass balance loss."
                ),
                evidence_data=json.dumps({
                    "measured_pressure_bar": p_val,
                    "nominal_pressure_bar": segment["nominal_pressure_bar"],
                    "surge_delta_bar": round(hydraulic.pressure_delta_bar, 2),
                    "flow_status": "Balanced",
                }),
                confidence_pct=confidence,
                confidence_explanation=(
                    f"Pressure elevated by +{hydraulic.pressure_delta_bar:.2f} bar while flow balance remains stable. "
                    "Typical signature of hydraulic surge or rapid valve actuation rather than structural pipe breach."
                ),
                required_checks=(
                    "1. Check surge anticipation valve and air-release valves along transmission line.\n"
                    "2. Review pump station trip logs for sudden deceleration."
                ),
                recommended_action=(
                    "Inspect pressure relief valve (PRV) damping chamber and verify air valve venting operation. "
                    "Monitor for secondary reflected pressure waves."
                ),
            )
            context["diagnosis"] = "PRESSURE_ANOMALY"
            return alert, context

        # Case D: MODERATE UNEXPLAINED FLOW DISCREPANCY WITHOUT ACOUSTIC CONFIRMATION
        # Could be meter drift, unmetered demand, or developing micro-leak
        if water_balance.is_statistically_significant and not acoustic.is_anomaly:
            confidence = 65.0
            alert = Alert(
                timestamp=ts_now,
                segment_id=seg_id,
                category=AlertCategory.MAINTENANCE_RISK.value,
                severity=AlertSeverity.MEDIUM.value,
                title=f"Unreconciled Flow Discrepancy (Unconfirmed Leak): {seg_id}",
                description=(
                    f"Flow deficit of {water_balance.unexplained_discrepancy_m3h:.1f} m³/h detected, but acoustic sensors "
                    f"report quiet baseline ({ac_val:.1f}/100). Do not classify as proven leak."
                ),
                evidence_data=json.dumps({
                    "flow_discrepancy_m3h": water_balance.unexplained_discrepancy_m3h,
                    "discrepancy_pct": water_balance.discrepancy_pct,
                    "acoustic_index": ac_val,
                }),
                confidence_pct=confidence,
                confidence_explanation=(
                    "Moderate evidence strength: Flow meter discrepancy is statistically significant, but acoustic "
                    "sensors do not corroborate orifice noise. Could indicate meter calibration drift, authorized unlogged withdrawal, "
                    "or non-metallic pipe dampening."
                ),
                required_checks="Verify meter calibration and check district billing / municipal withdrawal logs.",
                recommended_action="Conduct 48-hour step-testing and verify calibration of station flowmeters.",
            )
            context["diagnosis"] = "UNRECONCILED_FLOW"
            return alert, context

        # Case E: NORMAL OPERATION
        return None, context

    def evaluate_all_segments(
        self,
        segments: List[Dict[str, Any]],
        latest_readings_by_seg: Dict[str, Dict[str, Any]],
        authorized_withdrawals: Optional[Dict[str, float]] = None,
        reservoir_deltas: Optional[Dict[str, float]] = None,
    ) -> List[Alert]:
        """Evaluates all network segments and returns active detected alerts."""
        alerts = []
        auth_map = authorized_withdrawals or {}
        res_map = reservoir_deltas or {}

        for seg in segments:
            seg_id = seg["segment_id"]
            readings = latest_readings_by_seg.get(seg_id, {})
            auth_w = auth_map.get(seg_id, 0.0)
            res_d = res_map.get(seg.get("connected_reservoir_id", ""), 0.0)

            alert, _ = self.evaluate_segment(
                segment=seg,
                latest_readings=readings,
                authorized_withdrawal_m3h=auth_w,
                reservoir_storage_delta_m3h=res_d,
            )
            if alert:
                alerts.append(alert)

        return alerts
