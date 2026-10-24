"""
Main Executive Dashboard View
Presents top-level KPIs, reservoir status, system-wide hydraulic trends, active alert summaries,
and interactive simulation scenario switching.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

import config
from ui.components import render_header, render_disclaimer_banner, render_badge, apply_chart_theme
from simulation.scenarios import SimulationScenarioManager, ScenarioType


def render_dashboard_view(db, simulator, detection_engine, risk_engine):
    st.markdown("## 📊 Executive Overview Dashboard")
    # Duplicate disclaimer banner removed; centralized in top header

    # --- Scenario Switcher ---
    st.markdown("### 🎮 Simulation Condition Controller")
    scenarios = SimulationScenarioManager.get_all_scenarios()
    scenario_options = list(scenarios.keys())

    # Get or set current scenario in session state
    if "current_scenario" not in st.session_state:
        st.session_state["current_scenario"] = ScenarioType.NORMAL.value

    col_scen, col_desc = st.columns([1, 2])
    with col_scen:
        selected_scenario = st.selectbox(
            "Select Simulated Operational Condition:",
            options=scenario_options,
            index=scenario_options.index(st.session_state["current_scenario"]),
            format_func=lambda k: scenarios[k]["name"],
            key="dashboard_scenario_select"
        )
        if selected_scenario != st.session_state["current_scenario"]:
            st.session_state["current_scenario"] = selected_scenario
            st.rerun()

    scen_info = scenarios[selected_scenario]
    with col_desc:
        st.markdown(f"""
        <div class="scenario-box">
            <strong style="color: #0d9488;">Current Simulation State:</strong> {scen_info['name']}<br>
            <span style="font-size: 13px; color: #475569;">{scen_info['description']}</span>
        </div>
        """, unsafe_allow_html=True)

    # --- Fetch Live Data ---
    segments = db.get_all_segments()
    reservoirs = db.get_all_reservoirs()
    stations = db.get_all_stations()

    # Generate current readings using the selected scenario overrides
    now = datetime.now()
    scenario_overrides = scen_info.get("overrides", {})
    auth_withdrawals = scen_info.get("authorized_withdrawals_m3h", {})
    res_deltas = scen_info.get("reservoir_storage_delta_m3h", {})

    current_readings_by_seg = {}
    for seg in segments:
        snaps = simulator.generate_segment_snapshot(now, seg, scenario_overrides)
        seg_id = seg["segment_id"]
        current_readings_by_seg[seg_id] = {r.sensor_type: r.to_dict() for r in snaps}

    # Evaluate detection & risk across network
    active_alerts = []
    risk_results = []
    normal_count = 0
    attention_count = 0
    total_flow_in = 0.0
    total_unexplained_loss = 0.0

    for seg in segments:
        seg_id = seg["segment_id"]
        readings = current_readings_by_seg.get(seg_id, {})
        auth_w = auth_withdrawals.get(seg_id, 0.0)
        res_d = res_deltas.get(seg.get("connected_reservoir_id", ""), 0.0)

        alert, ctx = detection_engine.evaluate_segment(
            segment=seg,
            latest_readings=readings,
            authorized_withdrawal_m3h=auth_w,
            reservoir_storage_delta_m3h=res_d,
        )
        risk = risk_engine.evaluate_segment_risk(seg, ctx)
        risk_results.append(risk)

        if alert:
            active_alerts.append(alert)

        if risk.priority_category == "NORMAL":
            normal_count += 1
        else:
            attention_count += 1

        wb = ctx.get("water_balance")
        if wb:
            total_flow_in += wb.inflow_m3h
            if wb.is_statistically_significant and wb.unexplained_discrepancy_m3h > 0:
                total_unexplained_loss += wb.unexplained_discrepancy_m3h

    # Overall system metrics
    overall_discrepancy_pct = (total_unexplained_loss / total_flow_in * 100.0) if total_flow_in > 0 else 0.0
    suspected_leaks = [a for a in active_alerts if a.category in ("SUSPECTED_LEAK", "SUDDEN_BURST")]
    low_reservoirs = [r for r in reservoirs if r["current_storage_pct"] < r["low_level_threshold_pct"]]

    # --- KPI Metric Cards ---
    st.markdown("### 📈 Key Operational Indicators")
    k1, k2, k3, k4, k5 = st.columns(5)

    with k1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Pipeline Segments</div>
            <div class="metric-value">{len(segments)}</div>
            <div class="metric-delta" style="color: #059669;">
                ✔ {normal_count} Normal | ⚠ {attention_count} Flagged
            </div>
        </div>
        """, unsafe_allow_html=True)

    with k2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Suspected Leaks / Bursts</div>
            <div class="metric-value" style="color: {'#dc2626' if len(suspected_leaks) > 0 else '#0f172a'};">
                {len(suspected_leaks)}
            </div>
            <div class="metric-delta" style="color: {'#dc2626' if len(suspected_leaks) > 0 else '#64748b'};">
                {len(active_alerts)} Total System Alerts
            </div>
        </div>
        """, unsafe_allow_html=True)

    with k3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Unexplained Flow Deficit</div>
            <div class="metric-value" style="color: {'#ea580c' if total_unexplained_loss > 0 else '#0f172a'};">
                {total_unexplained_loss:.1f} <span style="font-size: 14px;">m³/h</span>
            </div>
            <div class="metric-delta" style="color: #64748b;">
                {overall_discrepancy_pct:.1f}% of gross inlet throughput
            </div>
        </div>
        """, unsafe_allow_html=True)

    with k4:
        low_res_count = len(low_reservoirs)
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Reservoir Storage Status</div>
            <div class="metric-value" style="color: {'#d97706' if low_res_count > 0 else '#0f172a'};">
                {low_res_count} Warnings
            </div>
            <div class="metric-delta" style="color: #64748b;">
                Across {len(reservoirs)} City Reservoirs
            </div>
        </div>
        """, unsafe_allow_html=True)

    with k5:
        # Sensor quality index
        healthy_sensor_pct = 100.0 if not any(a.category == "SENSOR_FAULT" for a in active_alerts) else 82.5
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Telemetry Health Index</div>
            <div class="metric-value" style="color: {'#059669' if healthy_sensor_pct > 90 else '#d97706'};">
                {healthy_sensor_pct:.1f}%
            </div>
            <div class="metric-delta" style="color: #64748b;">
                {len(stations)} Active Monitoring Stations
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- Hydraulic Trend Charts (Plotly) ---
    with st.expander("📈 View 12-Hour Network Hydraulic Telemetry Trends (Flow & Pressure)", expanded=False):
        st.caption("Granular real-time sensor streams and telemetry graphs are available in the dedicated '📡 Simulated Sensor Telemetry' view.")
        c_left, c_right = st.columns([1, 1])

        with c_left:
            # Flow trends across main segments
            fig_flow = go.Figure()
            colors = ["#0284c7", "#0ea5e9", "#059669", "#d97706", "#dc2626"]
            for idx, seg in enumerate(segments[:5]):
                seg_id = seg["segment_id"]
                # Build mini 12-hour synthetic trend
                hours = [h for h in range(12, 0, -1)]
                times = [f"-{h}h" for h in hours]
                base = seg["nominal_flow_m3h"]
                # Current offset
                offset = scenario_overrides.get(seg_id, {}).get("flow_offset", 0.0)
                values = [base * (0.85 + 0.15 * (h % 3) / 3.0) for h in hours[:-2]]
                values.extend([base + offset * 0.5, base + offset])

                fig_flow.add_trace(go.Scatter(
                    x=times,
                    y=values,
                    mode="lines+markers",
                    name=f"{seg_id} ({seg['name'][:18]}...)",
                    line={"color": colors[idx % len(colors)], "width": 2},
                    marker={"size": 4},
                ))

            fig_flow = apply_chart_theme(fig_flow, title="Flow Telemetry Trends (m³/h) Over Recent Hours")
            fig_flow.update_yaxes(title="Flow Rate (m³/h)")
            st.plotly_chart(fig_flow, use_container_width=True)

        with c_right:
            # Pressure trends across monitoring points
            fig_p = go.Figure()
            p_colors = ["#2563eb", "#0d9488", "#7c3aed", "#e11d48", "#b45309"]
            for idx, seg in enumerate(segments[:5]):
                seg_id = seg["segment_id"]
                hours = [h for h in range(12, 0, -1)]
                times = [f"-{h}h" for h in hours]
                base_p = seg["nominal_pressure_bar"]
                p_offset = scenario_overrides.get(seg_id, {}).get("pressure_offset", 0.0)
                p_values = [base_p + 0.05 * (h % 2) for h in hours[:-2]]
                p_values.extend([base_p + p_offset * 0.6, base_p + p_offset])

                fig_p.add_trace(go.Scatter(
                    x=times,
                    y=p_values,
                    mode="lines+markers",
                    name=f"{seg_id} (Nom: {base_p} bar)",
                    line={"color": p_colors[idx % len(p_colors)], "width": 2},
                    marker={"size": 4},
                ))

            # Add lower operating bound line
            fig_p.add_hline(
                y=config.THRESHOLDS["pressure_min_normal"],
                line_dash="dot",
                line_color="#ef4444",
                annotation_text="Service Minimum (2.5 bar)",
                annotation_position="bottom right",
            )
            fig_p = apply_chart_theme(fig_p, title="Pressure Telemetry Trends (bar) vs Nominal Envelope")
            fig_p.update_yaxes(title="Pressure (bar)")
            st.plotly_chart(fig_p, use_container_width=True)

    # --- City Reservoirs Status Table ---
    st.markdown("### 🏙️ City Reservoir Storage Levels")
    res_cols = st.columns(len(reservoirs))
    for idx, res in enumerate(reservoirs):
        with res_cols[idx]:
            pct = res["current_storage_pct"]
            is_low = pct < res["low_level_threshold_pct"]
            status_color = "#dc2626" if is_low else "#0284c7"
            status_text = "LOW WATER WARNING" if is_low else "Normal Storage"

            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{res['reservoir_id']}</div>
                <div style="font-weight: 600; font-size: 15px; color: #1e293b; margin-bottom: 8px;">
                    {res['name']}
                </div>
                <div style="display: flex; justify-content: space-between; align-items: baseline;">
                    <div style="font-size: 24px; font-weight: 700; color: {status_color};">
                        {pct:.1f}%
                    </div>
                    <div style="font-size: 13px; color: #64748b;">
                        {res['current_level_m']:.1f} m / {res['max_level_m']:.1f} m
                    </div>
                </div>
                <div style="margin-top: 10px; background: #e2e8f0; border-radius: 4px; height: 8px; overflow: hidden;">
                    <div style="background: {status_color}; width: {pct}%; height: 100%;"></div>
                </div>
                <div style="margin-top: 8px; font-size: 12px; font-weight: 600; color: {status_color};">
                    ● {status_text}
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- Maharashtra Lifeline Dams & Bulk Reservoirs ---
    st.markdown("### 🏞️ Maharashtra Lifeline Reservoirs (Regional Catchments)")
    maha_dams = [
        {"name": "Koyna Dam", "basin": "Krishna Basin", "pct": 96.4, "capacity": "2,797 M CM (~98.8 TMC)", "role": "Hydro & Western Maha"},
        {"name": "Jayakwadi (Nath Sagar)", "basin": "Godavari Basin", "pct": 84.2, "capacity": "2,909 M CM (~102.7 TMC)", "role": "Marathwada Agriculture & CSMC"},
        {"name": "Bhatsa Dam", "basin": "Ulhas Basin", "pct": 98.1, "capacity": "976 M CM (~34.5 TMC)", "role": "Chief Potable Source for Mumbai (BMC)"},
        {"name": "Ujani Dam (Bhima)", "basin": "Bhima Basin", "pct": 91.0, "capacity": "3,170 M CM (~112.0 TMC)", "role": "Solapur Drought Buffer & Cane Belt"},
        {"name": "Upper Vaitarna", "basin": "Vaitarna Basin", "pct": 95.8, "capacity": "331 M CM (~11.7 TMC)", "role": "Gravity Drinking Feed to Mumbai"},
        {"name": "Khadakwasla Complex", "basin": "Mutha Basin", "pct": 94.5, "capacity": "4 Dams (~29.1 TMC Combined)", "role": "Lifeline Supply for Pune City (PMC)"},
    ]

    m_cols1, m_cols2, m_cols3 = st.columns(3)
    for i, d in enumerate(maha_dams):
        target_col = m_cols1 if i % 3 == 0 else (m_cols2 if i % 3 == 1 else m_cols3)
        with target_col:
            color = "#059669" if d["pct"] >= 90 else ("#0284c7" if d["pct"] >= 75 else "#d97706")
            st.markdown(f"""
            <div class="dam-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <strong style="color: #0f172a; font-size: 14px;">{d['name']}</strong>
                    <span class="badge badge-normal">{d['basin']}</span>
                </div>
                <div style="font-size: 12px; color: #64748b; margin: 4px 0;">{d['capacity']}</div>
                <div style="display: flex; justify-content: space-between; align-items: baseline; margin: 6px 0 2px 0;">
                    <span style="font-size: 20px; font-weight: 700; color: {color};">{d['pct']}%</span>
                    <span style="font-size: 11px; color: #475569;">{d['role']}</span>
                </div>
                <div style="background: #e2e8f0; border-radius: 4px; height: 6px; overflow: hidden;">
                    <div style="background: {color}; width: {d['pct']}%; height: 100%;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- Active Incidents & High-Risk Pipeline Segments ---
    st.markdown("### 🚨 Active Alerts & Inspection Priorities")
    if active_alerts:
        for alert in active_alerts:
            severity_color = "#dc2626" if alert.severity == "CRITICAL" else ("#ea580c" if alert.severity == "HIGH" else "#d97706")
            st.markdown(f"""
            <div style="border-left: 5px solid {severity_color}; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px 18px; margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                    <strong style="font-size: 16px; color: #0f172a;">{alert.title}</strong>
                    <div>{render_badge(alert.severity)} {render_badge(alert.category)}</div>
                </div>
                <div style="font-size: 13px; color: #334155; margin-bottom: 8px;">
                    {alert.description}
                </div>
                <div style="font-size: 12px; background: #f8fafc; padding: 8px 12px; border-radius: 6px; color: #475569;">
                    <strong>Confidence ({alert.confidence_pct:.0f}%):</strong> {alert.confidence_explanation}<br>
                    <strong>Recommended Next Action:</strong> {alert.recommended_action}
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.success("✔ All pipeline segments and monitoring stations operating nominally. No active hydraulic or acoustic anomalies detected.")
