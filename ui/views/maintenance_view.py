"""
Predictive Maintenance & Inspection Management View
Provides work order tracking, inspection findings recording, condition assessment reviews,
and full maintenance workflow lifecycle (Pending -> Under Review -> Scheduled -> Completed).
"""
import streamlit as st
import pandas as pd
from datetime import datetime

import config
from ui.components import render_disclaimer_banner, render_badge
from models.maintenance import MaintenanceStatus, AssetConditionGrade


def render_maintenance_view(db, simulator, detection_engine, risk_engine):
    st.markdown("## 🛠️ Predictive Maintenance & Asset Management")
    render_disclaimer_banner()

    st.markdown("""
    <div style="font-size: 13px; color: #334155; margin-bottom: 20px;">
        <strong>Asset Integrity & Maintenance Workflow:</strong> Displays asset condition evaluations and manages work orders. 
        <em>Condition grades are diagnostic model assessments for prioritizing preventative maintenance, not physical forensic inspections. 
        No exact structural failure dates are claimed without continuous metallurgical coupon data.</em>
    </div>
    """, unsafe_allow_html=True)

    segments = db.get_all_segments()
    seg_dict = {s["segment_id"]: s for s in segments}

    tab_overview, tab_work_orders, tab_record_finding = st.tabs([
        "📋 Maintenance Prioritization",
        "📝 Work Orders & Status Updates",
        "🔍 Log New Field Inspection Finding",
    ])

    # --- TAB 1: MAINTENANCE PRIORITIZATION ---
    with tab_overview:
        st.markdown("### 🏆 Pipeline Segment Maintenance Rankings")
        now = datetime.now()
        current_scen_key = st.session_state.get("current_scenario", "NORMAL_OPERATION")
        from simulation.scenarios import SimulationScenarioManager
        scen_info = SimulationScenarioManager.get_scenario(current_scen_key)
        overrides = scen_info.get("overrides", {})

        maint_rows = []
        for s in segments:
            seg_id = s["segment_id"]
            snaps = simulator.generate_segment_snapshot(now, s, overrides)
            readings_map = {r.sensor_type: r.to_dict() for r in snaps}
            alert, ctx = detection_engine.evaluate_segment(s, readings_map)
            risk = risk_engine.evaluate_segment_risk(s, ctx)

            maint_rows.append({
                "Segment ID": seg_id,
                "Asset Name": s["name"],
                "Priority Score": f"{risk.priority_score:.1f} / 100",
                "Priority Category": risk.badge_label,
                "Estimated Asset Condition": risk.estimated_condition_grade,
                "Past Repairs": s["past_repair_count"],
                "Material": s["material"],
                "Age (Years)": s.get("age_years", 0),
                "Active Anomaly": alert.category if alert else "None (Normal)",
                "Recommended Action": risk.recommended_response,
            })

        maint_df = pd.DataFrame(maint_rows)
        st.dataframe(maint_df, use_container_width=True, hide_index=True)

    # --- TAB 2: WORK ORDERS & STATUS UPDATES ---
    with tab_work_orders:
        st.markdown("### 🔄 Active Work Orders & Maintenance Status")

        # Fetch records from DB
        records = db.get_maintenance_records()

        # If table is empty, auto-populate with initial records from risk evaluation
        if not records:
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for item in maint_rows[:4]:
                db.save_maintenance_record({
                    "segment_id": item["Segment ID"],
                    "priority_score": float(item["Priority Score"].split(" / ")[0]),
                    "priority_category": item["Priority Category"],
                    "estimated_condition": item["Estimated Asset Condition"],
                    "contributing_reasons": "Initial baseline asset inspection review",
                    "recommended_action": item["Recommended Action"],
                    "status": MaintenanceStatus.PENDING.value,
                    "assigned_to": "Unassigned",
                    "scheduled_date": "2026-11-15",
                    "notes": "Generated from baseline diagnostic screening",
                    "created_at": now_str,
                })
            records = db.get_maintenance_records()

        # Display current records
        if records:
            rec_display = []
            for r in records:
                rec_display.append({
                    "Record ID": r["record_id"],
                    "Segment ID": r["segment_id"],
                    "Priority Score": f"{r['priority_score']:.1f}",
                    "Condition Assessment": r["estimated_condition"],
                    "Status": r["status"],
                    "Assigned Technician": r.get("assigned_to", "Unassigned"),
                    "Scheduled Date": r.get("scheduled_date", "TBD"),
                    "Notes": r.get("notes", ""),
                    "Last Updated": r.get("updated_at", ""),
                })
            st.dataframe(pd.DataFrame(rec_display), use_container_width=True, hide_index=True)

        st.markdown("#### ✏️ Update Work Order Status")
        col_id, col_stat, col_tech = st.columns(3)

        with col_id:
            record_ids = [r["record_id"] for r in records] if records else [1]
            target_record_id = st.selectbox("Select Record ID to update:", options=record_ids)

        with col_stat:
            new_status = st.selectbox("Update Status:", options=[
                MaintenanceStatus.PENDING.value,
                MaintenanceStatus.UNDER_REVIEW.value,
                MaintenanceStatus.SCHEDULED.value,
                MaintenanceStatus.COMPLETED.value,
            ])

        with col_tech:
            new_technician = st.text_input("Assigned Technician / Contractor:", value="Field Team Alpha")

        col_date, col_notes = st.columns([1, 2])
        with col_date:
            new_sched_date = st.date_input("Scheduled Inspection Date:").strftime("%Y-%m-%d")
        with col_notes:
            update_notes = st.text_area("Maintenance Update Notes:", value="Reviewed hydraulic logs; scheduled field acoustic survey.")

        if st.button("💾 Save Maintenance Status Update", type="primary"):
            db.update_maintenance_status(
                record_id=target_record_id,
                status=new_status,
                notes=update_notes,
                assigned_to=new_technician,
                scheduled_date=new_sched_date,
            )
            st.success(f"Work order #{target_record_id} successfully updated to '{new_status}'!")
            st.rerun()

    # --- TAB 3: LOG NEW FIELD INSPECTION FINDING ---
    with tab_record_finding:
        st.markdown("### 📝 Record Field Inspection Finding")
        st.markdown("Authorized field engineers can record physical ground observations to calibrate the AI risk model.")

        with st.form("new_inspection_form"):
            c_seg, c_date = st.columns(2)
            with c_seg:
                insp_seg = st.selectbox("Pipeline Segment Inspected:", options=[s["segment_id"] for s in segments])
            with c_date:
                insp_date = st.date_input("Inspection Date:").strftime("%Y-%m-%d")

            c_name, c_leak = st.columns(2)
            with c_name:
                insp_name = st.text_input("Inspector Name & Credentials:", value="Marcus Vance (PE, Water Systems)")
            with c_leak:
                insp_leak = st.selectbox("Surface Leak / Ponding Observed?", options=["No", "Yes"])

            c_soil, c_cath = st.columns(2)
            with c_soil:
                insp_soil = st.selectbox("Soil Moisture Condition:", options=["Dry", "Damp", "Waterlogged / Saturated"])
            with c_cath:
                insp_cath = st.selectbox("Cathodic Protection Status:", options=["Good / Active", "Degraded / Depleted", "Absent / Not Installed"])

            insp_obs = st.text_area("Physical Observations:", value="Excavated inspection pit at chainage 2+400. Minor external graphitization on pipe exterior. Joint sealant intact.")
            insp_action = st.text_area("Immediate Actions Taken:", value="Cleaned pipe exterior and applied protective bituminous wrap.")
            insp_rec = st.text_area("Forward Recommendations:", value="Re-inspect in 24 months during scheduled district valve exercise.")

            submit_insp = st.form_submit_button("📥 Log Inspection Finding into SQLite Database")

            if submit_insp:
                finding_id = db.insert_inspection_finding({
                    "segment_id": insp_seg,
                    "inspection_date": insp_date,
                    "inspector_name": insp_name,
                    "physical_condition_observed": insp_obs,
                    "leak_detected": 1 if insp_leak == "Yes" else 0,
                    "soil_moisture_level": insp_soil,
                    "ground_movement_signs": 0,
                    "cathodic_protection_status": insp_cath,
                    "actions_taken": insp_action,
                    "recommendations": insp_rec,
                })
                st.success(f"Inspection finding #{finding_id} successfully logged for {insp_seg}!")
                st.rerun()

        # Previous inspection history
        st.markdown("#### 📜 Historical Inspection Log")
        past_findings = db.get_inspection_findings()
        if past_findings:
            st.dataframe(pd.DataFrame(past_findings), use_container_width=True, hide_index=True)
        else:
            st.info("No manual field inspection records logged yet.")
