"""
Alerts and Incident Management View
Facilitates triage, status acknowledgment, field technician dispatch, and resolution logging.
All incident actions persist directly to SQLite.
"""
import streamlit as st
import pandas as pd
from datetime import datetime

import config
from ui.components import render_disclaimer_banner, render_badge
from models.alert import IncidentStatus, AlertSeverity, AlertCategory


def render_alerts_view(db, detection_engine, simulator):
    st.markdown("## 🚨 Incident & Alert Triage Management")
    render_disclaimer_banner()

    # Sync any active detections from the current simulation into the SQLite DB if not already present
    segments = db.get_all_segments()
    current_scen_key = st.session_state.get("current_scenario", "NORMAL_OPERATION")
    from simulation.scenarios import SimulationScenarioManager
    scen_info = SimulationScenarioManager.get_scenario(current_scen_key)
    overrides = scen_info.get("overrides", {})
    auth_withdrawals = scen_info.get("authorized_withdrawals_m3h", {})
    res_deltas = scen_info.get("reservoir_storage_delta_m3h", {})

    now = datetime.now()
    active_alerts = []
    for s in segments:
        seg_id = s["segment_id"]
        snaps = simulator.generate_segment_snapshot(now, s, overrides)
        readings_map = {r.sensor_type: r.to_dict() for r in snaps}
        auth_w = auth_withdrawals.get(seg_id, 0.0)
        res_d = res_deltas.get(s.get("connected_reservoir_id", ""), 0.0)

        alert, _ = detection_engine.evaluate_segment(s, readings_map, authorized_withdrawal_m3h=auth_w, reservoir_storage_delta_m3h=res_d)
        if alert:
            active_alerts.append(alert)

    # Persist freshly detected alert into DB if not already there recently
    for a in active_alerts:
        existing = db.get_alerts(category=a.category, limit=5)
        # Check if an identical alert on this segment is already active in the DB
        has_active = any(ex["segment_id"] == a.segment_id and ex["status"] == "ACTIVE" for ex in existing)
        if not has_active:
            db.insert_alert(a.to_dict())

    # --- Filters ---
    st.markdown("### 🔍 Incident Triage Filters")
    col_status, col_cat, col_sev = st.columns(3)

    with col_status:
        status_filter = st.selectbox("Filter Status:", options=["ALL", "ACTIVE", "ACKNOWLEDGED", "INVESTIGATING", "RESOLVED", "FALSE_ALARM"])

    with col_cat:
        cat_filter = st.selectbox("Alert Category:", options=["ALL", "SUSPECTED_LEAK", "SUDDEN_BURST", "PRESSURE_ANOMALY", "SENSOR_FAULT", "MAINTENANCE_RISK"])

    with col_sev:
        sev_filter = st.selectbox("Severity Level:", options=["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW"])

    # Fetch alerts from SQLite
    db_alerts = db.get_alerts(
        status=status_filter if status_filter != "ALL" else None,
        category=cat_filter if cat_filter != "ALL" else None,
        limit=100,
    )

    if sev_filter != "ALL":
        db_alerts = [a for a in db_alerts if a["severity"] == sev_filter]

    # --- Incident List / Cards ---
    st.markdown(f"### 📋 Incident Records ({len(db_alerts)} Found)")

    if db_alerts:
        for alert in db_alerts:
            a_id = alert["alert_id"]
            sev = alert["severity"]
            status = alert["status"]
            sev_color = "#dc2626" if sev == "CRITICAL" else ("#ea580c" if sev == "HIGH" else "#d97706")

            with st.container():
                st.markdown(f"""
                <div style="border: 1px solid #e2e8f0; border-left: 6px solid {sev_color}; border-radius: 8px; padding: 16px 20px; margin-bottom: 14px; background: #ffffff;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <span style="font-size: 16px; font-weight: 700; color: #0f172a;">
                            #{a_id} — {alert['title']}
                        </span>
                        <div>
                            {render_badge(sev)} {render_badge(alert['category'])} {render_badge(status)}
                        </div>
                    </div>
                    <div style="font-size: 13px; color: #475569; margin-bottom: 8px;">
                        <strong>Segment:</strong> {alert['segment_id']} • <strong>Timestamp:</strong> {alert['timestamp']} • <strong>Assigned:</strong> {alert.get('assigned_technician') or 'Unassigned'}
                    </div>
                    <div style="font-size: 13px; color: #1e293b; margin-bottom: 10px;">
                        {alert['description']}
                    </div>
                    <div style="background: #f8fafc; border-radius: 6px; padding: 8px 12px; font-size: 12px; color: #334155; margin-bottom: 10px;">
                        <strong>Field Verification Check:</strong> {alert['required_checks']}<br>
                        <strong>Recommended Protocol:</strong> {alert['recommended_action']}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Incident Action Form
                with st.expander(f"⚙️ Triage & Update Incident #{a_id}"):
                    c1, c2 = st.columns(2)
                    with c1:
                        new_st = st.selectbox(
                            f"Update Incident Status (#{a_id}):",
                            options=[IncidentStatus.ACTIVE.value, IncidentStatus.ACKNOWLEDGED.value, IncidentStatus.INVESTIGATING.value, IncidentStatus.RESOLVED.value, IncidentStatus.FALSE_ALARM.value],
                            index=[IncidentStatus.ACTIVE.value, IncidentStatus.ACKNOWLEDGED.value, IncidentStatus.INVESTIGATING.value, IncidentStatus.RESOLVED.value, IncidentStatus.FALSE_ALARM.value].index(status),
                            key=f"status_sel_{a_id}"
                        )
                    with c2:
                        tech = st.text_input(
                            f"Assign Technician (#{a_id}):",
                            value=alert.get("assigned_technician") or "Rapid Response Unit 1",
                            key=f"tech_input_{a_id}"
                        )

                    notes = st.text_area(
                        f"Resolution & Field Investigation Notes (#{a_id}):",
                        value=alert.get("review_notes") or "",
                        key=f"notes_{a_id}"
                    )

                    if st.button(f"Update Incident #{a_id}", key=f"btn_update_{a_id}", type="primary"):
                        db.update_alert_status(a_id, new_st, notes=notes, technician=tech)
                        st.success(f"Incident #{a_id} updated successfully!")
                        st.rerun()
    else:
        st.info("No incident records matching the selected filter criteria.")
