"""
Water-Loss and Resource Conservation Analysis View
Evaluates mass conservation across transmission and distribution sectors:
Discrepancy = Inflow - Outflow - Storage Delta - Authorized Withdrawals
Includes meter uncertainty error bars (±2% tolerance) and honest labeling.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

import config
from ui.components import render_disclaimer_banner, apply_chart_theme
from simulation.scenarios import SimulationScenarioManager
from detection.water_balance import WaterBalanceCalculator


def render_water_balance_view(db, simulator):
    st.markdown("## 💧 Water-Loss & Resource Analysis")
    render_disclaimer_banner()

    st.markdown("""
    <div style="font-size: 13px; color: #334155; margin-bottom: 20px;">
        <strong>Mass-Balance Conservation Principle:</strong> Compares measured aggregate inflow, downstream consumer outflow, 
        storage reservoir dynamics, and authorized municipal permits. 
        <em>Discrepancies are categorized strictly as <strong>unexplained water-balance differences</strong> rather than confirmed leaks, 
        accounting for ±2% electromagnetic meter tolerance and unmetered fire/maintenance usage.</em>
    </div>
    """, unsafe_allow_html=True)

    segments = db.get_all_segments()
    reservoirs = db.get_all_reservoirs()

    # Active scenario context
    current_scen_key = st.session_state.get("current_scenario", "NORMAL_OPERATION")
    scen_info = SimulationScenarioManager.get_scenario(current_scen_key)
    overrides = scen_info.get("overrides", {})
    auth_withdrawals = scen_info.get("authorized_withdrawals_m3h", {})
    res_deltas = scen_info.get("reservoir_storage_delta_m3h", {})

    now = datetime.now()

    # Calculate segment-level balances
    balance_results = []
    for s in segments:
        seg_id = s["segment_id"]
        snaps = simulator.generate_segment_snapshot(now, s, overrides)
        readings_map = {r.sensor_type: r.to_dict() for r in snaps}

        f_in = readings_map.get("FLOW", {}).get("value", s["nominal_flow_m3h"])
        auth_w = auth_withdrawals.get(seg_id, 0.0)
        res_d = res_deltas.get(s.get("connected_reservoir_id", ""), 0.0)

        # In absence of dual flow meters on smaller lines, downstream is modeled via nominal minus loss
        offset = overrides.get(seg_id, {}).get("flow_offset", 0.0)
        outflow = s["nominal_flow_m3h"] if offset > 0 else (f_in if f_in else s["nominal_flow_m3h"])

        wb = WaterBalanceCalculator.calculate_balance(
            segment_id=seg_id,
            inflow_m3h=f_in or 0.0,
            outflow_m3h=outflow,
            storage_change_m3h=res_d,
            authorized_withdrawal_m3h=auth_w,
        )
        balance_results.append(wb)

    sys_summary = WaterBalanceCalculator.calculate_system_summary(balance_results)

    # --- KPI Tiles ---
    st.markdown("### 📊 System Volumetric Reconciliation")
    k1, k2, k3, k4 = st.columns(4)

    with k1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Measured Inflow</div>
            <div class="metric-value">{sys_summary['total_inflow_m3h']:.1f} <span style="font-size: 13px;">m³/h</span></div>
            <div class="metric-delta" style="color: #64748b;">Gross intake from WTP & Dam</div>
        </div>
        """, unsafe_allow_html=True)

    with k2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Measured Outflow</div>
            <div class="metric-value">{sys_summary['total_outflow_m3h']:.1f} <span style="font-size: 13px;">m³/h</span></div>
            <div class="metric-delta" style="color: #64748b;">Customer and DMA deliveries</div>
        </div>
        """, unsafe_allow_html=True)

    with k3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Net Storage & Authorized Permitted</div>
            <div class="metric-value">{sys_summary['total_storage_delta_m3h'] + sys_summary['total_authorized_m3h']:.1f} <span style="font-size: 13px;">m³/h</span></div>
            <div class="metric-delta" style="color: #64748b;">Storage: {sys_summary['total_storage_delta_m3h']:.1f} | Auth: {sys_summary['total_authorized_m3h']:.1f}</div>
        </div>
        """, unsafe_allow_html=True)

    with k4:
        disc = sys_summary["total_unexplained_discrepancy_m3h"]
        pct = sys_summary["overall_discrepancy_pct"]
        disc_color = "#dc2626" if disc > 20 else "#059669"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Unexplained Volumetric Difference</div>
            <div class="metric-value" style="color: {disc_color};">{disc:.1f} <span style="font-size: 13px;">m³/h</span></div>
            <div class="metric-delta" style="color: {disc_color}; font-weight: 600;">{pct:.1f}% Unreconciled</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- Volumetric Comparison Chart with Uncertainty Intervals ---
    st.markdown("### 📈 Segment-by-Segment Mass Balance & Uncertainty Intervals")

    chart_data = []
    for wb in balance_results:
        chart_data.append({
            "Segment": wb.segment_id,
            "Inflow": wb.inflow_m3h,
            "Outflow": wb.outflow_m3h,
            "Discrepancy": wb.unexplained_discrepancy_m3h,
            "Uncertainty": wb.uncertainty_band_m3h,
            "Significant": wb.is_statistically_significant,
        })
    df_wb = pd.DataFrame(chart_data)

    fig_wb = go.Figure()
    fig_wb.add_trace(go.Bar(
        name="Measured Inflow (m³/h)",
        x=df_wb["Segment"],
        y=df_wb["Inflow"],
        marker_color="#0284c7",
    ))
    fig_wb.add_trace(go.Bar(
        name="Accounted Outflow (m³/h)",
        x=df_wb["Segment"],
        y=df_wb["Outflow"],
        marker_color="#0ea5e9",
    ))
    fig_wb.add_trace(go.Scatter(
        name="Unexplained Difference (m³/h)",
        x=df_wb["Segment"],
        y=df_wb["Discrepancy"],
        mode="markers",
        marker={"color": "#ef4444", "size": 8, "symbol": "diamond"},
        error_y={
            "type": "data",
            "array": df_wb["Uncertainty"],
            "visible": True,
            "color": "#94a3b8",
            "thickness": 1.5,
            "width": 4,
        },
    ))

    fig_wb = apply_chart_theme(fig_wb, title="Segment Inflow vs Outflow with Composite Uncertainty Error Bars (±2%)", height=400)
    fig_wb.update_layout(barmode="group")
    fig_wb.update_yaxes(title="Volume Flow (m³/h)")
    st.plotly_chart(fig_wb, use_container_width=True)

    # --- Balance Table ---
    st.markdown("### 📋 Segment Mass-Conservation Audit Table")
    table_rows = []
    for wb in balance_results:
        table_rows.append({
            "Segment ID": wb.segment_id,
            "Inflow (m³/h)": f"{wb.inflow_m3h:.1f}",
            "Outflow (m³/h)": f"{wb.outflow_m3h:.1f}",
            "Storage Delta (m³/h)": f"{wb.storage_change_m3h:+.1f}",
            "Authorized Withdrawal (m³/h)": f"{wb.authorized_withdrawal_m3h:.1f}",
            "Unexplained Difference (m³/h)": f"{wb.unexplained_discrepancy_m3h:+.1f}",
            "Difference %": f"{wb.discrepancy_pct:.1f}%",
            "Meter Tolerance Band": f"±{wb.uncertainty_band_m3h:.1f} m³/h",
            "Statistical Significance": "⚠ Significant Loss" if wb.is_statistically_significant else "✔ Within Tolerance",
            "Status Description": wb.explanation,
        })

    st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- Maharashtra Municipal Non-Revenue Water (NRW) Benchmarks ---
    st.markdown("### 🏛️ Maharashtra Municipal NRW Benchmarks & Conservation Value")
    st.markdown("""
    In actual municipal operations across Maharashtra, unmetered physical leakage forms the largest component of Non-Revenue Water (NRW):
    """)

    nrw_c1, nrw_c2, nrw_c3 = st.columns(3)
    with nrw_c1:
        st.markdown("""
        <div class="dam-card">
            <strong style="color: #0f172a; font-size: 14px;">Greater Mumbai (BMC)</strong><br>
            <span style="font-size: 12px; color: #64748b;">Daily Supply: 3,850 MLD • NRW: ~25%–30%</span>
            <p style="font-size: 12px; color: #334155; margin: 6px 0 0 0;">
                Unaccounted volume represents ~950 MLD lost across 100+ km transmission trunks, aging cast-iron reticulation, and unmetered slum connections.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with nrw_c2:
        st.markdown("""
        <div class="dam-card">
            <strong style="color: #0f172a; font-size: 14px;">Pune City (PMC)</strong><br>
            <span style="font-size: 12px; color: #64748b;">Daily Supply: 1,600 MLD • NRW: ~32%</span>
            <p style="font-size: 12px; color: #334155; margin: 6px 0 0 0;">
                High transit loss between Khadakwasla raw conduit and fragmented distribution DMAs. Ongoing 24x7 smart metering seeks to curb loss to &lt;15%.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with nrw_c3:
        st.markdown("""
        <div class="dam-card">
            <strong style="color: #0f172a; font-size: 14px;">Chh. Sambhajinagar (CSMC)</strong><br>
            <span style="font-size: 12px; color: #64748b;">Daily Supply: ~200 MLD • NRW: ~35%</span>
            <p style="font-size: 12px; color: #334155; margin: 6px 0 0 0;">
                Single 45 km pipeline from Jayakwadi experiences frequent bursts and joint leaks under high pump heads, causing intermittent weekly rationing.
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div style="background: #f0fdfa; border: 1px solid #99f6e4; border-radius: 8px; padding: 12px 16px; margin-top: 14px; font-size: 12px; color: #0f766e;">
        <strong>💡 Conservation Impact:</strong> Reducing physical pipe breaches by just <strong>10%</strong> across a 1,000 MLD transmission network recovers <strong>100,000 m³ per day</strong>. This saves hundreds of megawatt-hours in high-lift pumping electricity and extends dam storage into peak summer months without requiring new dam construction.
    </div>
    """, unsafe_allow_html=True)
