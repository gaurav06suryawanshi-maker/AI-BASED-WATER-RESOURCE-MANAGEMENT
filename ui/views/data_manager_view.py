"""
Data Management, Import/Export, and Demo Data Lifecycle View
Provides secure CSV import with schema validation, CSV report exports,
and a guarded reset-to-demo-data feature.
"""
import streamlit as st
import pandas as pd
from datetime import datetime

import config
from ui.components import render_disclaimer_banner
from utils.csv_handler import CSVHandler


def render_data_manager_view(db):
    st.markdown("## 💾 Data Management & Telemetry Import/Export")
    render_disclaimer_banner()

    st.markdown("""
    <div style="font-size: 13px; color: #334155; margin-bottom: 20px;">
        <strong>Data Governance & Provenance:</strong> Manage simulated telemetry, import user-supplied CSV datasets, 
        download engineering reports, and maintain database state. 
        <em>Imported telemetry is validated against engineering ranges before entry into SQLite storage.</em>
    </div>
    """, unsafe_allow_html=True)

    tab_import, tab_export, tab_templates, tab_reset = st.tabs([
        "📥 CSV Telemetry & Asset Import",
        "📤 CSV Reports Export",
        "📄 Documented CSV Schemas & Templates",
        "🔄 Database Reset & Demo Seed",
    ])

    # --- TAB 1: CSV IMPORT ---
    with tab_import:
        st.markdown("### 📥 Import Data from CSV")
        import_type = st.radio("Select dataset type to upload:", ["Pipeline Asset Specifications", "Sensor Telemetry Readings"], horizontal=True)

        uploaded_file = st.file_uploader(f"Choose {import_type} CSV File:", type=["csv"])

        if uploaded_file is not None:
            content = uploaded_file.getvalue()
            st.info(f"File uploaded: **{uploaded_file.name}** ({len(content)} bytes)")

            if import_type == "Pipeline Asset Specifications":
                is_valid, df_parsed, errors = CSVHandler.validate_and_parse_assets(content)

                if is_valid and df_parsed is not None:
                    st.success("✔ Validation Passed! File matches required schema.")
                    st.markdown("#### Preview Data to Import:")
                    st.dataframe(df_parsed.head(10), use_container_width=True)

                    if st.button("Confirm and Import Pipeline Assets into SQLite", type="primary"):
                        with db.get_connection() as conn:
                            cursor = conn.cursor()
                            for _, r in df_parsed.iterrows():
                                cursor.execute("""
                                    INSERT OR REPLACE INTO pipeline_segments (
                                        segment_id, name, stage, upstream_station_id, downstream_station_id,
                                        length_km, diameter_mm, material, installation_year, nominal_pressure_bar,
                                        nominal_flow_m3h, criticality, soil_condition, burial_depth_m,
                                        past_repair_count, last_inspection_date, nearby_excavation_risk, connected_reservoir_id
                                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                                """, (
                                    r["segment_id"], r["name"], r["stage"], r["upstream_station_id"], r["downstream_station_id"],
                                    float(r["length_km"]), int(r["diameter_mm"]), r["material"], int(r["installation_year"]),
                                    float(r["nominal_pressure_bar"]), float(r["nominal_flow_m3h"]), r["criticality"],
                                    r.get("soil_condition", "Moderate"), float(r.get("burial_depth_m", 1.5)),
                                    int(r.get("past_repair_count", 0)), r.get("last_inspection_date"),
                                    int(r.get("nearby_excavation_risk", 0)), r.get("connected_reservoir_id")
                                ))
                            conn.commit()
                        st.success(f"Successfully imported {len(df_parsed)} pipeline assets!")
                        st.rerun()
                else:
                    st.error("❌ Validation Failed. Please fix the following errors:")
                    for err in errors:
                        st.write(f"- {err}")

            else:  # Sensor Telemetry Readings
                is_valid, df_parsed, errors = CSVHandler.validate_and_parse_readings(content)

                if is_valid and df_parsed is not None:
                    st.success("✔ Validation Passed! Telemetry headers and formats are valid.")
                    st.markdown("#### Preview Telemetry Data:")
                    st.dataframe(df_parsed.head(10), use_container_width=True)

                    if st.button("Confirm and Insert Readings into Telemetry Stream", type="primary"):
                        readings_data = df_parsed.to_dict(orient="records")
                        db.insert_sensor_readings(readings_data)
                        st.success(f"Successfully inserted {len(readings_data)} sensor readings into the database!")
                        st.rerun()
                else:
                    st.error("❌ Validation Failed:")
                    for err in errors:
                        st.write(f"- {err}")

    # --- TAB 2: CSV EXPORT ---
    with tab_export:
        st.markdown("### 📤 Export System Data to CSV")
        st.write("Generate clean, structured CSV files for auditing, reporting, or external analytics.")

        c_exp1, c_exp2, c_exp3 = st.columns(3)

        with c_exp1:
            st.markdown("#### 📡 Sensor Telemetry")
            telemetry_recs = db.get_telemetry_history(limit=1000)
            if telemetry_recs:
                df_t = pd.DataFrame(telemetry_recs)
                csv_t = df_t.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="📥 Download Telemetry CSV",
                    data=csv_t,
                    file_name=f"waterguard_telemetry_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                )
            else:
                st.info("No telemetry records to export.")

        with c_exp2:
            st.markdown("#### 🚨 Alerts & Incidents")
            alerts_recs = db.get_alerts(limit=500)
            if alerts_recs:
                df_a = pd.DataFrame(alerts_recs)
                csv_a = df_a.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="📥 Download Alerts Log CSV",
                    data=csv_a,
                    file_name=f"waterguard_incidents_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                )
            else:
                st.info("No alert records to export.")

        with c_exp3:
            st.markdown("#### 🛠️ Maintenance Work Orders")
            maint_recs = db.get_maintenance_records()
            if maint_recs:
                df_m = pd.DataFrame(maint_recs)
                csv_m = df_m.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="📥 Download Maintenance CSV",
                    data=csv_m,
                    file_name=f"waterguard_maintenance_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                )
            else:
                st.info("No maintenance work orders to export.")

    # --- TAB 3: DOCUMENTED CSV SCHEMAS & TEMPLATES ---
    with tab_templates:
        st.markdown("### 📄 Documented CSV Templates & Units")
        st.write("Download sample CSV templates pre-filled with valid headers and example data.")

        t1, t2 = st.columns(2)
        with t1:
            st.markdown("#### Pipeline Asset Specifications")
            st.code("""
Columns:
- segment_id: Unique string ID (e.g. TX-101)
- name: Human readable descriptive name
- stage: Transmission, Distribution, or Intake
- upstream_station_id: Upstream monitoring station ID
- downstream_station_id: Downstream station ID
- length_km: Float length in kilometers
- diameter_mm: Integer pipe inner diameter (mm)
- material: Ductile Iron, Cast Iron, Steel, HDPE, etc.
- installation_year: Year of installation (e.g. 2005)
- nominal_pressure_bar: Standard operating pressure (bar)
- nominal_flow_m3h: Standard operating flow (m³/h)
- criticality: Critical, High, Medium, or Low
- soil_condition: Non-corrosive, Moderate, Corrosive
- past_repair_count: Number of previous physical repairs
- nearby_excavation_risk: 0 or 1
            """, language="yaml")
            st.download_button(
                label="📥 Download Asset Template CSV",
                data=CSVHandler.get_sample_assets_csv(),
                file_name="pipeline_assets_template.csv",
                mime="text/csv",
            )

        with t2:
            st.markdown("#### Sensor Telemetry Stream")
            st.code("""
Columns:
- timestamp: ISO-8601 string (YYYY-MM-DD HH:MM:SS)
- station_id: Monitoring station ID (e.g. MS-02)
- segment_id: Associated pipeline segment ID (e.g. TX-101)
- sensor_type: PRESSURE, FLOW, ACOUSTIC, VIBRATION, or RESERVOIR_LEVEL
- value: Float measurement (e.g. 5.82)
- unit: bar, m³/h, Index (0-100), mm/s, or m
- health_status: HEALTHY, DEGRADED, FROZEN, MISSING, DELAYED, or UNREALISTIC
- is_synthetic: 1 (synthetic) or 0 (real hardware)
- flag_notes: Optional string annotation
            """, language="yaml")
            st.download_button(
                label="📥 Download Telemetry Template CSV",
                data=CSVHandler.get_sample_readings_csv(),
                file_name="sensor_readings_template.csv",
                mime="text/csv",
            )

    # --- TAB 4: RESET DATABASE TO DEMO ---
    with tab_reset:
        st.markdown("### 🔄 Reset System to Default Demo State")
        st.warning("""
        **CAUTION:** Resetting will erase all user-imported telemetry, custom work orders, 
        and logged incident resolutions. It will reseed the original default prototype topology.
        """)

        confirm_reset = st.checkbox("I understand that custom prototype data will be cleared and replaced with default demo assets.")

        if st.button("🚨 Reset Database to Factory Demo Data", type="primary", disabled=not confirm_reset):
            db.reset_database()
            st.success("Database has been reset to default demo topology!")
            st.rerun()
