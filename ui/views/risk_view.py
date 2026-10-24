"""
Risk-to-Response Intelligence View
Displays explainable pipeline inspection priority scores (0-100), contributing factor breakdowns,
and targeted engineering maintenance recommendations.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

import config
from ui.components import render_disclaimer_banner, render_badge, apply_chart_theme
from simulation.scenarios import SimulationScenarioManager


def render_risk_view(db, simulator, detection_engine, risk_engine):
    st.markdown("## ⚖️ Risk-to-Response Inspection Intelligence")
    render_disclaimer_banner()

    st.markdown("""
    <div style="font-size: 13px; color: #334155; margin-bottom: 20px;">
        <strong>Explainable Risk Framework:</strong> The Inspection Priority Score (0–100 index) is an engineering decision-support tool. 
        It systematically decouples <strong>Immediate Hydraulic & Acoustic Anomalies (up to 55 pts)</strong> from 
        <strong>Long-Term Physical Asset Deterioration (up to 45 pts)</strong>. 
        <em>It is an inspection prioritization metric, not an unverified probability of failure.</em>
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

    # Generate current readings and evaluate risk
    risk_results = []
    for seg in segments:
        snaps = simulator.generate_segment_snapshot(now, seg, overrides)
        readings_map = {r.sensor_type: r.to_dict() for r in snaps}
        seg_id = seg["segment_id"]
        auth_w = auth_withdrawals.get(seg_id, 0.0)
        res_d = res_deltas.get(seg.get("connected_reservoir_id", ""), 0.0)

        alert, ctx = detection_engine.evaluate_segment(seg, readings_map, authorized_withdrawal_m3h=auth_w, reservoir_storage_delta_m3h=res_d)
        risk = risk_engine.evaluate_segment_risk(seg, ctx)
        risk_results.append({
            "segment": seg,
            "risk": risk,
            "alert": alert,
        })

    # Sort segments by priority score descending
    risk_results.sort(key=lambda x: x["risk"].priority_score, reverse=True)

    # --- Stacked Bar Chart: Factor Breakdown Across All Segments ---
    st.markdown("### 📊 System-Wide Inspection Priority Breakdown")

    chart_rows = []
    for item in risk_results:
        r = item["risk"]
        s = item["segment"]
        fb = r.factor_breakdown
        chart_rows.append({
            "Segment": f"{s['segment_id']} ({s['material'][:4]})",
            "Active Hydraulic Imbalance": fb.get("active_hydraulic_imbalance", 0),
            "Acoustic Evidence": fb.get("acoustic_evidence", 0),
            "Asset Age & Material": fb.get("asset_age_material", 0),
            "Failure / Repair History": fb.get("incident_history", 0),
            "Criticality & Excavation": fb.get("criticality_consequence", 0),
        })

    df_chart = pd.DataFrame(chart_rows)

    fig_stack = go.Figure()
    fig_stack.add_trace(go.Bar(name="Active Flow/Pressure Deficit", x=df_chart["Segment"], y=df_chart["Active Hydraulic Imbalance"], marker_color="#ef4444"))
    fig_stack.add_trace(go.Bar(name="Acoustic Cavitation/Noise", x=df_chart["Segment"], y=df_chart["Acoustic Evidence"], marker_color="#f97316"))
    fig_stack.add_trace(go.Bar(name="Asset Material & Age", x=df_chart["Segment"], y=df_chart["Asset Age & Material"], marker_color="#0284c7"))
    fig_stack.add_trace(go.Bar(name="Historical Repairs", x=df_chart["Segment"], y=df_chart["Failure / Repair History"], marker_color="#8b5cf6"))
    fig_stack.add_trace(go.Bar(name="Criticality Consequence", x=df_chart["Segment"], y=df_chart["Criticality & Excavation"], marker_color="#10b981"))

    fig_stack.update_layout(barmode="stack")
    fig_stack = apply_chart_theme(fig_stack, title="Inspection Priority Score (0–100) Factor Decomposition", height=380)
    fig_stack.update_yaxes(range=[0, 105], title="Composite Score (0-100)")
    st.plotly_chart(fig_stack, use_container_width=True)

    # --- Ranked Segment Priority Table ---
    st.markdown("### 📋 Segment Inspection Priority League Table")
    table_rows = []
    for item in risk_results:
        r = item["risk"]
        s = item["segment"]
        table_rows.append({
            "Priority Score": f"{r.priority_score:.1f} / 100",
            "Category": r.badge_label,
            "Segment ID": s["segment_id"],
            "Asset Name": s["name"],
            "Material": s["material"],
            "Age": f"{s.get('age_years', 0)} yrs",
            "Immediate Telemetry Score": f"{r.immediate_anomaly_score:.1f} / 55",
            "Long-Term Asset Score": f"{r.long_term_asset_score:.1f} / 45",
            "Estimated Condition Grade": r.estimated_condition_grade,
        })

    st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)

    # --- Detailed Segment Explanations Accordion ---
    st.markdown("### 🔎 Individual Segment Explainability & Recommended Responses")
    for item in risk_results:
        r = item["risk"]
        s = item["segment"]
        seg_id = s["segment_id"]

        with st.expander(f"{seg_id} — {s['name']} | Priority: {r.priority_score:.1f} ({r.priority_category})"):
            c_info, c_rec = st.columns([1, 1])
            with c_info:
                st.markdown(f"**Physical Condition Rating (Model-Derived):**<br>*{r.estimated_condition_grade}*", unsafe_allow_html=True)
                st.markdown("**Contributing Risk Factors:**")
                for reason in r.contributing_reasons:
                    st.markdown(f"- {reason}")
            with c_rec:
                st.markdown("**Actionable Engineering Recommendation:**")
                st.info(r.recommended_response)
                st.markdown(f"""
                <div style="font-size: 12px; color: #64748b; background: #f8fafc; padding: 10px; border-radius: 6px;">
                    <strong>Asset Summary:</strong> {s['material']} • {s['diameter_mm']} mm diameter • {s['length_km']} km length • {s['past_repair_count']} past repairs • Soil: {s['soil_condition']}
                </div>
                """, unsafe_allow_html=True)
