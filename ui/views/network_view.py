"""
Interactive Pipeline Network Schematic Visualization
Renders topological node-link schematic with hydraulic condition highlights,
interactive segment selection, telemetry deep-dive, risk factors, and recommended maintenance.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

import config
from simulation.network_topology import NetworkTopology
from ui.components import render_disclaimer_banner, render_badge, apply_chart_theme


def render_network_view(db, simulator, detection_engine, risk_engine):
    st.markdown("## 🗺️ Pipeline Network Schematic & Topology")
    render_disclaimer_banner()

    st.markdown("""
    <div style="font-size: 13px; color: #475569; margin-bottom: 16px;">
        <strong>Schematic Graph Model:</strong> Illustrates the end-to-end municipal water transmission lifecycle from 
        <strong>Water Source / Dam → Water Treatment Plant → Main Transmission Pipeline → Monitoring Stations → City Reservoirs → Distribution Network</strong>.
        Segments are color-coded by their real-time inspection priority and hydraulic condition.
    </div>
    """, unsafe_allow_html=True)

    # Fetch network data
    nodes = NetworkTopology.get_schematic_nodes()
    edges = NetworkTopology.get_schematic_edges()
    segments = db.get_all_segments()
    seg_dict = {s["segment_id"]: s for s in segments}

    # Current simulation condition from session state
    current_scen_key = st.session_state.get("current_scenario", "NORMAL_OPERATION")
    scen_overrides = db.get_segment  # dummy
    from simulation.scenarios import SimulationScenarioManager
    scen_info = SimulationScenarioManager.get_scenario(current_scen_key)
    overrides = scen_info.get("overrides", {})
    auth_withdrawals = scen_info.get("authorized_withdrawals_m3h", {})
    res_deltas = scen_info.get("reservoir_storage_delta_m3h", {})

    # Evaluate all segments for status coloring
    now = datetime.now()
    seg_evaluations = {}
    for s in segments:
        seg_id = s["segment_id"]
        snaps = simulator.generate_segment_snapshot(now, s, overrides)
        readings_map = {r.sensor_type: r.to_dict() for r in snaps}
        auth_w = auth_withdrawals.get(seg_id, 0.0)
        res_d = res_deltas.get(s.get("connected_reservoir_id", ""), 0.0)

        alert, ctx = detection_engine.evaluate_segment(s, readings_map, authorized_withdrawal_m3h=auth_w, reservoir_storage_delta_m3h=res_d)
        risk = risk_engine.evaluate_segment_risk(s, ctx)
        seg_evaluations[seg_id] = {
            "alert": alert,
            "risk": risk,
            "context": ctx,
            "readings": readings_map,
        }

    # Build Plotly schematic graph
    node_x = [n["x"] for n in nodes]
    node_y = [n["y"] for n in nodes]
    node_text = [f"<b>{n['name']}</b><br>Type: {n['type']}<br>Stage: {n['stage']}<br>{n['desc']}" for n in nodes]
    node_colors = [n["color"] for n in nodes]

    node_dict = {n["id"]: n for n in nodes}

    view_mode = st.radio(
        "Display Network Visualization Mode:",
        [
            "📍 Verified Maharashtra Dam-to-City Transmission Map (GIS Corridors)",
            "🗺️ 2D Topological Hydraulic Schematic",
            "🌐 Interactive 3D Pipeline Network (with Elevation Profile)",
        ],
        horizontal=True,
    )

    if view_mode == "📍 Verified Maharashtra Dam-to-City Transmission Map (GIS Corridors)":
        gis_data = NetworkTopology.get_maharashtra_gis_network()
        gis_nodes = gis_data["nodes"]
        gis_corridors = gis_data["corridors"]
        gis_node_dict = {n["id"]: n for n in gis_nodes}

        fig_gis = go.Figure()

        # Draw verified transmission pipelines
        for corr in gis_corridors:
            fn = gis_node_dict.get(corr["from_id"])
            tn = gis_node_dict.get(corr["to_id"])
            if fn and tn:
                hover_txt = (
                    f"<b>Transmission Pipeline: {corr['name']}</b><br>"
                    f"From: {fn['name']} ({fn['elev_m']}m ASL)<br>"
                    f"To: {tn['name']} ({tn['elev_m']}m ASL)<br>"
                    f"Distance: {corr['distance_km']} km<br>"
                    f"Diameter: {corr['diameter_mm']} mm<br>"
                    f"Material: {corr['material']}<br>"
                    f"Daily Flow: {corr['capacity_mld']} MLD<br>"
                    f"Conveyance Type: {corr['type']}"
                )
                fig_gis.add_trace(go.Scatter(
                    x=[fn["lon"], tn["lon"]],
                    y=[fn["lat"], tn["lat"]],
                    mode="lines",
                    line=dict(color=corr["color"], width=4),
                    hoverinfo="text",
                    text=hover_txt,
                    name=corr["name"],
                    showlegend=False,
                ))

        # Draw facility nodes
        node_lons = [n["lon"] for n in gis_nodes]
        node_lats = [n["lat"] for n in gis_nodes]
        node_hover = [
            f"<b>{n['name']}</b> ({n['type']})<br>"
            f"Coordinates: {n['lat']}°N, {n['lon']}°E | Elevation: {n['elev_m']} m ASL<br>"
            f"Capacity / Scope: {n['capacity']}<br>"
            f"Primary Municipal Role: {n['role']}<br>"
            f"Regional Sector: {n['corridor']}"
            for n in gis_nodes
        ]

        fig_gis.add_trace(go.Scatter(
            x=node_lons,
            y=node_lats,
            mode="markers+text",
            marker=dict(
                size=[n["size"] for n in gis_nodes],
                color=[n["color"] for n in gis_nodes],
                symbol=[n["symbol"] for n in gis_nodes],
                line=dict(width=2, color="#ffffff"),
            ),
            text=[n["name"].split(" (")[0] for n in gis_nodes],
            textposition="top right",
            textfont=dict(size=11, color="#0f172a", family="Inter, sans-serif"),
            hoverinfo="text",
            hovertext=node_hover,
            name="Water Facilities",
            showlegend=False,
        ))

        # Custom Legend for node types
        fig_gis.add_trace(go.Scatter(x=[None], y=[None], mode="markers", marker=dict(size=12, color="#0284c7", symbol="circle"), name="Catchment Dams & Reservoirs"))
        fig_gis.add_trace(go.Scatter(x=[None], y=[None], mode="markers", marker=dict(size=12, color="#0ea5e9", symbol="square"), name="Water Treatment Works (WTP)"))
        fig_gis.add_trace(go.Scatter(x=[None], y=[None], mode="markers", marker=dict(size=12, color="#059669", symbol="diamond"), name="Municipal Consumers (BMC / PMC / CSMC / SMC)"))
        fig_gis.add_trace(go.Scatter(x=[None], y=[None], mode="markers", marker=dict(size=12, color="#0d9488", symbol="triangle-up"), name="Agricultural / Regional Off-takes"))

        fig_gis.update_layout(
            title={
                "text": "<b>Verified Maharashtra Bulk Water Transmission Corridors (GIS Coordinates)</b>",
                "font": {"size": 15, "color": "#0f172a", "family": "Inter, sans-serif"}
            },
            xaxis=dict(
                title="Longitude (°E)",
                range=[72.3, 76.6],
                showgrid=True,
                gridcolor="#f1f5f9"
            ),
            yaxis=dict(
                title="Latitude (°N)",
                range=[17.0, 20.3],
                showgrid=True,
                gridcolor="#f1f5f9"
            ),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            plot_bgcolor="#f8fafc",
            paper_bgcolor="#ffffff",
            height=540,
            margin=dict(l=50, r=40, t=60, b=40),
        )

        st.plotly_chart(fig_gis, use_container_width=True)

        st.markdown("""
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-left: 4px solid #0284c7; border-radius: 0 8px 8px 0; padding: 10px 16px; margin-bottom: 16px; font-size: 12px; color: #475569;">
            <strong>📍 Verified Geographic Infrastructure Note:</strong> Locations, dam capacities, WTP outputs, and pipeline diameters represent verified engineering data from Maharashtra Water Resources Department (WRD), Brihanmumbai Municipal Corporation (BMC Water Supply), and Pune Municipal Corporation (PMC). Telemetry readings and pressure losses on monitored segments are generated via physical simulation models for research and evaluation.
        </div>
        """, unsafe_allow_html=True)

        # Transmission Corridor Summary Cards
        st.markdown("##### 🚰 Key Maharashtra Transmission Corridors")
        c_m1, c_m2, c_m3 = st.columns(3)
        with c_m1:
            st.markdown("""
            <div class="dam-card">
                <strong style="color: #0f172a; font-size: 14px;">Bhatsa ➔ Panjrapur ➔ Mumbai</strong><br>
                <span style="font-size: 12px; color: #64748b;">Distance: ~76.5 km • Diameter: 2,400–3,000 mm MS</span>
                <p style="font-size: 12px; color: #334155; margin: 6px 0 0 0;">
                    Transports ~2,400 MLD of raw and treated water into Bhandup Complex for Greater Mumbai.
                </p>
            </div>
            """, unsafe_allow_html=True)
        with c_m2:
            st.markdown("""
            <div class="dam-card">
                <strong style="color: #0f172a; font-size: 14px;">Khadakwasla ➔ Parvati ➔ Pune</strong><br>
                <span style="font-size: 12px; color: #64748b;">Distance: ~22 km • Diameter: 2,500 mm Twin Conduit</span>
                <p style="font-size: 12px; color: #334155; margin: 6px 0 0 0;">
                    Closed twin conduit conveys ~1,000 MLD to Parvati and Warje water treatment works feeding Pune city.
                </p>
            </div>
            """, unsafe_allow_html=True)
        with c_m3:
            st.markdown("""
            <div class="dam-card">
                <strong style="color: #0f172a; font-size: 14px;">Jayakwadi ➔ Nakshatrawadi ➔ Sambhajinagar</strong><br>
                <span style="font-size: 12px; color: #64748b;">Distance: ~53.5 km • Diameter: 1,400 mm MS</span>
                <p style="font-size: 12px; color: #334155; margin: 6px 0 0 0;">
                    High-head single-stage pumped pipeline supplying ~200 MLD to Marathwada's industrial and drinking grid.
                </p>
            </div>
            """, unsafe_allow_html=True)

    elif view_mode == "🌐 Interactive 3D Pipeline Network (with Elevation Profile)":
        # 3D Pipeline Network
        fig_3d = go.Figure()

        # Draw 3D pipeline links (edges)
        for edge in edges:
            from_n = node_dict.get(edge["from_node"])
            to_n = node_dict.get(edge["to_node"])
            seg_id = edge.get("segment_id")

            if from_n and to_n:
                eval_info = seg_evaluations.get(seg_id)
                edge_color = eval_info["risk"].badge_color if eval_info else "#94a3b8"
                edge_width = 6 if eval_info and eval_info["risk"].priority_score >= 60 else 4
                hover_text = (
                    f"<b>Segment: {seg_id}</b><br>"
                    f"Elevation Drop: {from_n['z']:.0f}m ➔ {to_n['z']:.0f}m (Δ {abs(from_n['z'] - to_n['z']):.0f}m)<br>"
                    f"Priority: {eval_info['risk'].badge_label if eval_info else 'Normal'}<br>"
                    f"Pressure: {eval_info['readings'].get('PRESSURE', {}).get('value', 'N/A') if eval_info else 'N/A'} bar<br>"
                    f"Flow: {eval_info['readings'].get('FLOW', {}).get('value', 'N/A') if eval_info else 'N/A'} m³/h"
                )

                fig_3d.add_trace(go.Scatter3d(
                    x=[from_n["x"], to_n["x"]],
                    y=[from_n["y"], to_n["y"]],
                    z=[from_n["z"], to_n["z"]],
                    mode="lines",
                    line={"width": edge_width, "color": edge_color},
                    hoverinfo="text",
                    text=hover_text,
                    name=edge["label"],
                    showlegend=False,
                ))

        # Draw 3D nodes
        node_z = [n["z"] for n in nodes]
        fig_3d.add_trace(go.Scatter3d(
            x=node_x,
            y=node_y,
            z=node_z,
            mode="markers+text",
            marker={
                "size": 7,
                "color": node_colors,
                "symbol": "circle",
                "opacity": 0.95,
            },
            text=[f"{n['id']} ({n['z']:.0f}m)" for n in nodes],
            textposition="top center",
            textfont={"size": 10, "color": "#0f172a"},
            hoverinfo="text",
            hovertext=[f"<b>{n['name']}</b><br>Elevation: {n['z']:.1f} m<br>Type: {n['type']}<br>{n['desc']}" for n in nodes],
            name="Facilities & Stations",
        ))

        # Add 3D Legend items
        for tier_key, tier_data in config.PRIORITY_TIERS.items():
            fig_3d.add_trace(go.Scatter3d(
                x=[None],
                y=[None],
                z=[None],
                mode="lines",
                line={"width": 5, "color": tier_data["color"]},
                name=tier_data["badge"],
            ))

        fig_3d.update_layout(
            title={
                "text": "3D Pipeline Network Model (Coordinates & Physical Elevation in Meters)",
                "font": {"size": 15, "color": "#0f172a", "family": "Inter, sans-serif"},
            },
            scene={
                "xaxis_title": "Network Grid X",
                "yaxis_title": "Network Grid Y",
                "zaxis_title": "Elevation (meters ASL)",
                "camera": {
                    "eye": {"x": 1.4, "y": -1.4, "z": 0.8},
                },
                "bgcolor": "#f8fafc",
            },
            height=560,
            margin={"l": 20, "r": 20, "t": 50, "b": 20},
        )
        st.plotly_chart(fig_3d, use_container_width=True)

    else:
        # Draw 2D schematic graph
        fig = go.Figure()

        # Draw pipeline links (edges)
        for edge in edges:
            from_n = node_dict.get(edge["from_node"])
            to_n = node_dict.get(edge["to_node"])
            seg_id = edge.get("segment_id")

            if from_n and to_n:
                eval_info = seg_evaluations.get(seg_id)
                if eval_info:
                    edge_color = eval_info["risk"].badge_color
                    edge_width = 4 if eval_info["risk"].priority_score >= 60 else 3
                    hover_text = (
                        f"<b>Segment: {seg_id}</b><br>"
                        f"Priority: {eval_info['risk'].badge_label} ({eval_info['risk'].priority_score}/100)<br>"
                        f"Condition: {eval_info['risk'].estimated_condition_grade}<br>"
                        f"Flow: {eval_info['readings'].get('FLOW', {}).get('value', 'N/A')} m³/h<br>"
                        f"Pressure: {eval_info['readings'].get('PRESSURE', {}).get('value', 'N/A')} bar"
                    )
                else:
                    edge_color = "#94a3b8"
                    edge_width = 2
                    hover_text = f"Link: {edge['label']}"

                # Link line trace
                fig.add_trace(go.Scatter(
                    x=[from_n["x"], to_n["x"]],
                    y=[from_n["y"], to_n["y"]],
                    mode="lines",
                    line={"width": edge_width, "color": edge_color},
                    hoverinfo="text",
                    text=hover_text,
                    showlegend=False,
                ))

                # Midpoint edge label
                mid_x = (from_n["x"] + to_n["x"]) / 2.0
                mid_y = (from_n["y"] + to_n["y"]) / 2.0
                fig.add_trace(go.Scatter(
                    x=[mid_x],
                    y=[mid_y],
                    mode="text",
                    text=[edge["label"]],
                    textposition="top center",
                    textfont={"size": 10, "color": "#334155", "family": "Inter, sans-serif"},
                    hoverinfo="none",
                    showlegend=False,
                ))

        # Draw nodes
        fig.add_trace(go.Scatter(
            x=node_x,
            y=node_y,
            mode="markers+text",
            marker={
                "size": 22,
                "color": node_colors,
                "line": {"width": 2, "color": "#ffffff"},
                "symbol": "circle",
            },
            text=[n["id"] for n in nodes],
            textposition="bottom center",
            textfont={"size": 11, "color": "#0f172a", "family": "Inter, sans-serif", "weight": "bold"},
            hoverinfo="text",
            hovertext=node_text,
            name="Network Facilities",
        ))

        # Add legend items for risk tiers
        for tier_key, tier_data in config.PRIORITY_TIERS.items():
            fig.add_trace(go.Scatter(
                x=[None],
                y=[None],
                mode="lines",
                line={"width": 4, "color": tier_data["color"]},
                name=tier_data["badge"],
            ))

        fig = apply_chart_theme(fig, title="Schematic Network Graph — Water Journey Telemetry", height=500)
        fig.update_xaxes(showgrid=False, zeroline=False, showticklabels=False)
        fig.update_yaxes(showgrid=False, zeroline=False, showticklabels=False)
        st.plotly_chart(fig, use_container_width=True)

    # --- Interactive Segment Deep-Dive Section ---
    st.markdown("### 🔎 Pipeline Segment Telemetry & Risk Inspector")
    seg_names = [f"{s['segment_id']} — {s['name']}" for s in segments]
    selected_seg_str = st.selectbox("Choose a pipeline segment to inspect details:", options=seg_names, index=0)
    selected_seg_id = selected_seg_str.split(" — ")[0]

    chosen_seg = seg_dict.get(selected_seg_id)
    chosen_eval = seg_evaluations.get(selected_seg_id)

    if chosen_seg and chosen_eval:
        risk_res = chosen_eval["risk"]
        readings_map = chosen_eval["readings"]
        alert = chosen_eval["alert"]
        ctx = chosen_eval["context"]

        col_left, col_right = st.columns([1, 1])

        with col_left:
            st.markdown(f"#### 📋 Asset Metadata: {chosen_seg['segment_id']}")
            m1, m2 = st.columns(2)
            with m1:
                st.write(f"**Segment Name:** {chosen_seg['name']}")
                st.write(f"**Stage:** {chosen_seg['stage']}")
                st.write(f"**Material:** {chosen_seg['material']}")
                st.write(f"**Diameter:** {chosen_seg['diameter_mm']} mm")
                st.write(f"**Length:** {chosen_seg['length_km']} km")
            with m2:
                st.write(f"**Installation Year:** {chosen_seg['installation_year']} ({chosen_seg.get('age_years', 0)} yrs)")
                st.write(f"**Nominal Pressure:** {chosen_seg['nominal_pressure_bar']} bar")
                st.write(f"**Nominal Flow:** {chosen_seg['nominal_flow_m3h']} m³/h")
                st.write(f"**Criticality Tier:** {chosen_seg['criticality']}")
                st.write(f"**Past Repairs:** {chosen_seg['past_repair_count']} recorded")

            st.markdown("#### ⚡ Real-Time Sensor Telemetry")
            telemetry_rows = []
            for s_type, r in readings_map.items():
                val_display = f"{r['value']} {r['unit']}" if r.get("value") is not None else "N/A (Missing)"
                telemetry_rows.append({
                    "Sensor Modality": s_type,
                    "Reading": val_display,
                    "Health Status": r["health_status"],
                    "Station ID": r["station_id"],
                    "Timestamp": r["timestamp"],
                })
            st.dataframe(pd.DataFrame(telemetry_rows), use_container_width=True, hide_index=True)

        with col_right:
            st.markdown(f"#### 🎯 Risk Score: {risk_res.priority_score} / 100")
            st.markdown(f"**Priority Category:** {render_badge(risk_res.priority_category)}", unsafe_allow_html=True)
            st.markdown(f"**Estimated Condition:** *{risk_res.estimated_condition_grade}*")

            # Risk Factor Breakdown Bar Chart
            factors = risk_res.factor_breakdown
            factor_df = pd.DataFrame([
                {"Factor": "Active Hydraulic Deficit", "Points": factors.get("active_hydraulic_imbalance", 0), "Max": 35},
                {"Factor": "Acoustic / Vibration Evidence", "Points": factors.get("acoustic_evidence", 0), "Max": 20},
                {"Factor": "Asset Age & Material", "Points": factors.get("asset_age_material", 0), "Max": 20},
                {"Factor": "Incident & Failure History", "Points": factors.get("incident_history", 0), "Max": 15},
                {"Factor": "Criticality & Consequence", "Points": factors.get("criticality_consequence", 0), "Max": 10},
            ])

            fig_bar = go.Figure()
            fig_bar.add_trace(go.Bar(
                x=factor_df["Points"],
                y=factor_df["Factor"],
                orientation="h",
                marker={"color": "#0ea5e9"},
                text=[f"{p:.1f} pts" for p in factor_df["Points"]],
                textposition="auto",
            ))
            fig_bar = apply_chart_theme(fig_bar, title="Inspection Priority Factor Points Contribution", height=240)
            fig_bar.update_xaxes(range=[0, 40], title="Points")
            st.plotly_chart(fig_bar, use_container_width=True)

            st.markdown("#### 💡 Explainable Reasons & Recommended Action")
            for reason in risk_res.contributing_reasons:
                st.markdown(f"- {reason}")

            st.info(f"**Engineering Recommendation:**\n{risk_res.recommended_response}")
