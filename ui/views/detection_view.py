"""
Leak and Anomaly Detection Engine View
Provides transparent multi-indicator decision verification, false-positive filtering analysis,
and actionable incident diagnosis.
"""
import streamlit as st
import pandas as pd
import json
from datetime import datetime

import config
from ui.components import render_disclaimer_banner, render_badge
from simulation.scenarios import SimulationScenarioManager


def render_detection_view(db, simulator, detection_engine):
    st.markdown("## 🔍 Multi-Indicator Anomaly & Leak Detection")
    render_disclaimer_banner()

    st.markdown("""
    <div style="font-size: 13px; color: #334155; margin-bottom: 20px;">
        <strong>Multi-Variable Cross-Validation:</strong> The detection engine correlates four independent physical dimensions:
        <strong>(1) Sensor Quality Filtering</strong>, <strong>(2) Volumetric Mass-Balance</strong>, 
        <strong>(3) Hydraulic Pressure Gradient</strong>, and <strong>(4) Acoustic Orifice Signatures</strong>.
        A single sensor fluctuation does not trigger an alarm.
    </div>
    """, unsafe_allow_html=True)

    # Fetch network data
    segments = db.get_all_segments()
    current_scen_key = st.session_state.get("current_scenario", "NORMAL_OPERATION")
    scen_info = SimulationScenarioManager.get_scenario(current_scen_key)
    overrides = scen_info.get("overrides", {})
    auth_withdrawals = scen_info.get("authorized_withdrawals_m3h", {})
    res_deltas = scen_info.get("reservoir_storage_delta_m3h", {})

    now = datetime.now()

    # Generate current readings
    readings_by_seg = {}
    for seg in segments:
        snaps = simulator.generate_segment_snapshot(now, seg, overrides)
        readings_by_seg[seg["segment_id"]] = {r.sensor_type: r.to_dict() for r in snaps}

    # Evaluate all segments
    all_evaluations = []
    active_alerts = []

    for seg in segments:
        seg_id = seg["segment_id"]
        readings = readings_by_seg.get(seg_id, {})
        auth_w = auth_withdrawals.get(seg_id, 0.0)
        res_d = res_deltas.get(seg.get("connected_reservoir_id", ""), 0.0)

        alert, ctx = detection_engine.evaluate_segment(
            segment=seg,
            latest_readings=readings,
            authorized_withdrawal_m3h=auth_w,
            reservoir_storage_delta_m3h=res_d,
        )
        if alert:
            active_alerts.append(alert)

        all_evaluations.append({
            "segment_id": seg_id,
            "name": seg["name"],
            "diagnosis": ctx.get("diagnosis", "NORMAL"),
            "quality": ctx.get("quality_report"),
            "water_balance": ctx.get("water_balance"),
            "hydraulic": ctx.get("hydraulic"),
            "acoustic": ctx.get("acoustic"),
            "alert": alert,
        })

    # --- Active Detected Anomalies List ---
    st.markdown(f"### 🚨 Active Telemetry Detections ({len(active_alerts)} Alerts)")
    if active_alerts:
        for alert in active_alerts:
            sev_color = "#dc2626" if alert.severity == "CRITICAL" else ("#ea580c" if alert.severity == "HIGH" else "#d97706")
            with st.container():
                st.markdown(f"""
                <div style="border: 1px solid #e2e8f0; border-left: 6px solid {sev_color}; border-radius: 10px; padding: 18px 22px; margin-bottom: 16px; background: #ffffff; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <span style="font-size: 18px; font-weight: 700; color: #0f172a;">{alert.title}</span>
                        <div>{render_badge(alert.severity)} {render_badge(alert.category)}</div>
                    </div>
                    <div style="font-size: 14px; color: #334155; margin-bottom: 12px;">
                        {alert.description}
                    </div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; background: #f8fafc; padding: 12px 16px; border-radius: 8px; font-size: 13px; color: #1e293b; margin-bottom: 12px;">
                        <div>
                            <strong>Detection Started:</strong> {alert.timestamp}<br>
                            <strong>Evidence Strength:</strong> {alert.confidence_pct:.0f}% Confidence<br>
                            <strong>Confidence Rationale:</strong> {alert.confidence_explanation}
                        </div>
                        <div>
                            <strong>Additional Field Checks Required:</strong><br>
                            {alert.required_checks}
                        </div>
                    </div>
                    <div style="font-size: 13px; color: #0369a1; background: #f0f9ff; padding: 10px 14px; border-radius: 6px; border-left: 3px solid #0284c7;">
                        <strong>Recommended Protocol:</strong> {alert.recommended_action}
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.success("✔ No active hydraulic anomalies or leak patterns detected in the current telemetry snapshot.")

    # --- Multi-Indicator Evidence Matrix ---
    st.markdown("### 📊 Cross-Validation Modality Evidence Matrix")
    st.markdown("""
    Shows how the engine evaluated each modality across all monitored segments. Notice how legitimate demand, 
    authorized withdrawals, and sensor faults are correctly isolated rather than misdiagnosed as pipe leaks.
    """)

    matrix_rows = []
    for item in all_evaluations:
        s_id = item["segment_id"]
        q = item["quality"]
        wb = item["water_balance"]
        h = item["hydraulic"]
        ac = item["acoustic"]

        q_status = "✔ Healthy" if (q and q.is_valid_for_analysis) else "❌ Hardware Fault"
        wb_status = f"{wb.unexplained_discrepancy_m3h:.1f} m³/h ({wb.status_label})" if wb else "N/A"
        h_status = f"{h.pressure_delta_bar:+.2f} bar ({h.anomaly_type})" if h else "N/A"
        ac_status = f"Index {ac.acoustic_index:.1f} ({ac.anomaly_type})" if ac else "N/A"

        matrix_rows.append({
            "Segment ID": s_id,
            "Asset Name": item["name"],
            "Diagnosis Result": item["diagnosis"],
            "Data Quality Filter": q_status,
            "Mass-Balance Discrepancy": wb_status,
            "Hydraulic Pressure Delta": h_status,
            "Acoustic Orifice Index": ac_status,
        })

    st.dataframe(pd.DataFrame(matrix_rows), use_container_width=True, hide_index=True)

    # --- False-Positive Discrimination Case Studies ---
    with st.expander("ℹ️ How WaterGuard AI Prevents False Alarms (Design Principles)"):
        st.markdown("""
        1. **Distinguishing Legitimate Customer Demand from Leakage:**
           - High customer demand causes *both* upstream inflow and downstream outflow to rise symmetrically.
           - Friction head loss increases naturally according to Hazen-Williams, but acoustic baseline remains quiet.
           - WaterGuard AI flags this as *NORMAL DEMAND* rather than a volumetric leak.
        
        2. **Preventing Sensor Blips from Triggering Alarms:**
           - A sudden stuck zero-standard-deviation flatline is flagged as `SENSOR_FAULT (FROZEN)`.
           - Negative pressure or astronomical flow is flagged as `SENSOR_FAULT (UNREALISTIC)`.
           - Physical maintenance is recommended for the transducer, while the segment is marked `Insufficient Data` rather than declaring a pipe breach.

        3. **Accounting for Known Withdrawals and Tank Storage:**
           - Scheduled hydrant flushing and reservoir filling introduce flow imbalances.
           - WaterGuard AI integrates permitted withdrawal permits ($W_{auth}$) and reservoir level changes ($\Delta S$) directly into the mass-conservation equation before testing for unexplained deficits.
        """)
