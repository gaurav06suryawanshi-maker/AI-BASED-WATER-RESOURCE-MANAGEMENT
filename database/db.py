"""
SQLite Database Layer for WaterGuard AI
Handles persistent storage for topology, telemetry, alerts, and maintenance records.
"""
import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import config


class DatabaseManager:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = str(db_path or config.DATABASE_PATH)
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def init_db(self) -> None:
        """Initializes tables and indexes if they do not exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Water Sources
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS water_sources (
                source_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                source_type TEXT NOT NULL,
                capacity_m3 REAL NOT NULL,
                current_storage_pct REAL NOT NULL,
                safe_yield_m3h REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'Operating'
            );
            """)

            # Treatment Plants
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS treatment_plants (
                plant_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                source_id TEXT NOT NULL,
                design_capacity_m3h REAL NOT NULL,
                current_throughput_m3h REAL NOT NULL,
                chlorine_residual_ppm REAL DEFAULT 1.2,
                turbidity_ntu REAL DEFAULT 0.35,
                status TEXT NOT NULL DEFAULT 'Operating',
                FOREIGN KEY(source_id) REFERENCES water_sources(source_id)
            );
            """)

            # Pipeline Segments
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS pipeline_segments (
                segment_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                stage TEXT NOT NULL,
                upstream_station_id TEXT NOT NULL,
                downstream_station_id TEXT NOT NULL,
                length_km REAL NOT NULL,
                diameter_mm INTEGER NOT NULL,
                material TEXT NOT NULL,
                installation_year INTEGER NOT NULL,
                nominal_pressure_bar REAL NOT NULL,
                nominal_flow_m3h REAL NOT NULL,
                criticality TEXT NOT NULL,
                soil_condition TEXT DEFAULT 'Moderate',
                burial_depth_m REAL DEFAULT 1.5,
                past_repair_count INTEGER DEFAULT 0,
                last_inspection_date TEXT,
                nearby_excavation_risk INTEGER DEFAULT 0,
                connected_reservoir_id TEXT
            );
            """)

            # Monitoring Stations
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS monitoring_stations (
                station_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                segment_id TEXT NOT NULL,
                stage TEXT NOT NULL,
                elevation_m REAL NOT NULL,
                has_pressure_sensor INTEGER DEFAULT 1,
                has_flow_meter INTEGER DEFAULT 1,
                has_acoustic_sensor INTEGER DEFAULT 1,
                has_reservoir_sensor INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1
            );
            """)

            # Reservoirs
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS reservoirs (
                reservoir_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                connected_segment_id TEXT NOT NULL,
                capacity_m3 REAL NOT NULL,
                current_level_m REAL NOT NULL,
                max_level_m REAL NOT NULL,
                current_storage_pct REAL NOT NULL,
                low_level_threshold_pct REAL DEFAULT 25.0,
                status TEXT DEFAULT 'Normal'
            );
            """)

            # Sensor Telemetry
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS sensor_readings (
                reading_id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                station_id TEXT NOT NULL,
                segment_id TEXT NOT NULL,
                sensor_type TEXT NOT NULL,
                value REAL,
                unit TEXT NOT NULL,
                health_status TEXT NOT NULL DEFAULT 'HEALTHY',
                is_synthetic INTEGER NOT NULL DEFAULT 1,
                flag_notes TEXT
            );
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_readings_ts ON sensor_readings(timestamp);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_readings_segment ON sensor_readings(segment_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_readings_station ON sensor_readings(station_id);")

            # Alerts & Incidents
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                segment_id TEXT NOT NULL,
                category TEXT NOT NULL,
                severity TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                evidence_data TEXT NOT NULL,
                confidence_pct REAL NOT NULL,
                confidence_explanation TEXT NOT NULL,
                required_checks TEXT NOT NULL,
                recommended_action TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'ACTIVE',
                review_notes TEXT,
                assigned_technician TEXT,
                resolved_at TEXT
            );
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_segment ON alerts(segment_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status);")

            # Predictive Maintenance Records
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS maintenance_records (
                record_id INTEGER PRIMARY KEY AUTOINCREMENT,
                segment_id TEXT NOT NULL,
                priority_score REAL NOT NULL,
                priority_category TEXT NOT NULL,
                estimated_condition TEXT NOT NULL,
                contributing_reasons TEXT NOT NULL,
                recommended_action TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Pending',
                assigned_to TEXT,
                scheduled_date TEXT,
                notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_maint_segment ON maintenance_records(segment_id);")

            # Inspection Findings
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS inspection_findings (
                finding_id INTEGER PRIMARY KEY AUTOINCREMENT,
                segment_id TEXT NOT NULL,
                inspection_date TEXT NOT NULL,
                inspector_name TEXT NOT NULL,
                physical_condition_observed TEXT NOT NULL,
                leak_detected INTEGER NOT NULL DEFAULT 0,
                soil_moisture_level TEXT NOT NULL,
                ground_movement_signs INTEGER NOT NULL DEFAULT 0,
                cathodic_protection_status TEXT NOT NULL,
                actions_taken TEXT NOT NULL,
                recommendations TEXT NOT NULL
            );
            """)

            # System Settings / Audit Metadata
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """)

            conn.commit()

        # Seed initial network topology if table is empty
        self._seed_default_topology_if_empty()

    def _seed_default_topology_if_empty(self) -> None:
        """Seeds default topology representing the simulated water journey."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) AS cnt FROM pipeline_segments;")
            if cursor.fetchone()["cnt"] > 0:
                return  # already seeded

            # 1. Water Sources
            sources = [
                ("SRC-DAM-01", "Pine Valley Dam", "Dam Reservoir", 12500000.0, 78.4, 4500.0, "Operating"),
                ("SRC-RIV-02", "Clearwater River Intake", "River Intake", 5000000.0, 84.1, 2200.0, "Operating"),
            ]
            cursor.executemany("""
                INSERT INTO water_sources (source_id, name, source_type, capacity_m3, current_storage_pct, safe_yield_m3h, status)
                VALUES (?, ?, ?, ?, ?, ?, ?);
            """, sources)

            # 2. Water Treatment Plant
            plants = [
                ("WTP-MAIN", "Central Water Treatment Works", "SRC-DAM-01", 3500.0, 2450.0, 1.25, 0.28, "Operating"),
            ]
            cursor.executemany("""
                INSERT INTO treatment_plants (plant_id, name, source_id, design_capacity_m3h, current_throughput_m3h, chlorine_residual_ppm, turbidity_ntu, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """, plants)

            # 3. Reservoirs
            reservoirs = [
                ("RES-NORTH", "North Hill Elevated Reservoir", "TX-102", 45000.0, 8.2, 10.0, 82.0, 25.0, "Normal"),
                ("RES-SOUTH", "South Valley Storage Reservoir", "TX-103", 60000.0, 2.1, 12.0, 17.5, 25.0, "Low Storage Warning"),
            ]
            cursor.executemany("""
                INSERT INTO reservoirs (reservoir_id, name, connected_segment_id, capacity_m3, current_level_m, max_level_m, current_storage_pct, low_level_threshold_pct, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, reservoirs)

            # 4. Monitoring Stations
            stations = [
                ("MS-01", "Pine Valley Intake Station", "TX-100", "Intake", 312.0, 1, 1, 1, 0, 1),
                ("MS-02", "WTP Effluent Discharge Station", "TX-101", "Transmission", 275.0, 1, 1, 1, 0, 1),
                ("MS-03", "Ridge Junction Booster Station", "TX-102", "Transmission", 290.0, 1, 1, 1, 0, 1),
                ("MS-04", "North Hill Inflow Monitoring", "TX-102", "Transmission", 305.0, 1, 1, 1, 1, 1),
                ("MS-05", "South Valley Trunk Flowmeter", "TX-103", "Transmission", 220.0, 1, 1, 1, 1, 1),
                ("MS-06", "Metro East Distribution Gateway", "DN-201", "Distribution", 185.0, 1, 1, 1, 0, 1),
                ("MS-07", "Commercial District Metered Area", "DN-202", "Distribution", 170.0, 1, 1, 1, 0, 1),
                ("MS-08", "Industrial Park Sub-Network Hub", "DN-203", "Distribution", 165.0, 1, 1, 1, 0, 1),
                ("MS-09", "Old Quarter Heritage Distribution", "DN-204", "Distribution", 195.0, 1, 1, 1, 0, 1),
            ]
            cursor.executemany("""
                INSERT INTO monitoring_stations (station_id, name, segment_id, stage, elevation_m, has_pressure_sensor, has_flow_meter, has_acoustic_sensor, has_reservoir_sensor, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, stations)

            # 5. Pipeline Segments
            # Reflecting realistic assets with varying ages, materials, and conditions
            segments = [
                ("TX-100", "Raw Water Intake Line", "Intake", "MS-01", "MS-02", 4.2, 1000, "Steel", 2012, 4.2, 2500.0, "Critical", "Moderate", 2.2, 0, "2025-08-14", 0, None),
                ("TX-101", "Main High-Pressure Transmission Trunk", "Transmission", "MS-02", "MS-03", 6.8, 900, "Ductile Iron", 2005, 5.8, 2400.0, "Critical", "Moderate", 2.0, 1, "2025-11-02", 0, None),
                ("TX-102", "North Reservoir Feeder Main", "Transmission", "MS-03", "MS-04", 5.1, 750, "Ductile Iron", 2008, 4.8, 1150.0, "High", "Non-corrosive", 1.8, 0, "2026-02-19", 0, "RES-NORTH"),
                ("TX-103", "South Valley Transmission Aqueduct", "Transmission", "MS-03", "MS-05", 8.4, 800, "Prestressed Concrete", 1994, 5.2, 1250.0, "Critical", "Corrosive", 2.1, 3, "2025-04-10", 1, "RES-SOUTH"),
                ("DN-201", "Metro East Residential Sector Feeder", "Distribution", "MS-04", "MS-06", 3.6, 500, "HDPE", 2018, 3.8, 620.0, "Medium", "Non-corrosive", 1.4, 0, "2026-05-12", 0, None),
                ("DN-202", "Commercial District Metered Area", "Distribution", "MS-06", "MS-07", 2.9, 400, "Ductile Iron", 2010, 3.6, 480.0, "High", "Moderate", 1.5, 1, "2025-09-30", 0, None),
                ("DN-203", "Industrial Zone Heavy Flow Loop", "Distribution", "MS-05", "MS-08", 4.5, 600, "Steel", 2002, 4.1, 720.0, "High", "Corrosive", 1.6, 2, "2025-07-21", 0, None),
                ("DN-204", "Old Quarter Heritage Reticulation", "Distribution", "MS-07", "MS-09", 3.2, 300, "Cast Iron", 1978, 3.2, 280.0, "Critical", "Corrosive", 1.2, 5, "2024-10-15", 1, None),
            ]
            cursor.executemany("""
                INSERT INTO pipeline_segments (
                    segment_id, name, stage, upstream_station_id, downstream_station_id,
                    length_km, diameter_mm, material, installation_year, nominal_pressure_bar,
                    nominal_flow_m3h, criticality, soil_condition, burial_depth_m,
                    past_repair_count, last_inspection_date, nearby_excavation_risk, connected_reservoir_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, segments)

            # Metadata
            cursor.execute("""
                INSERT OR REPLACE INTO system_metadata (key, value, updated_at)
                VALUES ('initialized_at', ?, ?);
            """, (datetime.now().isoformat(), datetime.now().isoformat()))

            conn.commit()

    # --- Query & Persistence Helpers ---

    def get_all_segments(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM pipeline_segments ORDER BY stage, segment_id;")
            return [dict(row) for row in cursor.fetchall()]

    def get_segment(self, segment_id: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM pipeline_segments WHERE segment_id = ?;", (segment_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_all_stations(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM monitoring_stations ORDER BY station_id;")
            return [dict(row) for row in cursor.fetchall()]

    def get_all_reservoirs(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM reservoirs ORDER BY reservoir_id;")
            return [dict(row) for row in cursor.fetchall()]

    def update_reservoir_storage(self, reservoir_id: str, current_level_m: float, storage_pct: float, status: str) -> None:
        with self.get_connection() as conn:
            conn.execute("""
                UPDATE reservoirs
                SET current_level_m = ?, current_storage_pct = ?, status = ?
                WHERE reservoir_id = ?;
            """, (current_level_m, storage_pct, status, reservoir_id))
            conn.commit()

    def get_sources_and_plants(self) -> Dict[str, Any]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM water_sources;")
            sources = [dict(r) for r in cursor.fetchall()]
            cursor.execute("SELECT * FROM treatment_plants;")
            plants = [dict(r) for r in cursor.fetchall()]
            return {"sources": sources, "plants": plants}

    # --- Telemetry Readings ---

    def insert_sensor_readings(self, readings: List[Dict[str, Any]]) -> None:
        with self.get_connection() as conn:
            conn.executemany("""
                INSERT INTO sensor_readings (
                    timestamp, station_id, segment_id, sensor_type, value, unit, health_status, is_synthetic, flag_notes
                ) VALUES (
                    :timestamp, :station_id, :segment_id, :sensor_type, :value, :unit, :health_status, :is_synthetic, :flag_notes
                );
            """, readings)
            conn.commit()

    def get_latest_readings_by_segment(self) -> Dict[str, Dict[str, Any]]:
        """Returns the most recent reading for each sensor type per segment."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT sr.*
                FROM sensor_readings sr
                INNER JOIN (
                    SELECT segment_id, sensor_type, MAX(timestamp) as max_ts
                    FROM sensor_readings
                    GROUP BY segment_id, sensor_type
                ) latest ON sr.segment_id = latest.segment_id 
                         AND sr.sensor_type = latest.sensor_type 
                         AND sr.timestamp = latest.max_ts;
            """)
            rows = cursor.fetchall()
            result: Dict[str, Dict[str, Any]] = {}
            for r in rows:
                seg = r["segment_id"]
                if seg not in result:
                    result[seg] = {}
                result[seg][r["sensor_type"]] = dict(r)
            return result

    def get_telemetry_history(self, segment_id: Optional[str] = None, sensor_type: Optional[str] = None, limit: int = 500) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM sensor_readings WHERE 1=1"
            params = []
            if segment_id:
                query += " AND segment_id = ?"
                params.append(segment_id)
            if sensor_type:
                query += " AND sensor_type = ?"
                params.append(sensor_type)
            query += " ORDER BY timestamp DESC LIMIT ?;"
            params.append(limit)
            cursor.execute(query, params)
            return [dict(r) for r in cursor.fetchall()]

    def count_sensor_readings(self) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as cnt FROM sensor_readings;")
            return cursor.fetchone()["cnt"]

    # --- Alerts ---

    def insert_alert(self, alert_data: Dict[str, Any]) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO alerts (
                    timestamp, segment_id, category, severity, title, description,
                    evidence_data, confidence_pct, confidence_explanation, required_checks,
                    recommended_action, status, review_notes, assigned_technician, resolved_at
                ) VALUES (
                    :timestamp, :segment_id, :category, :severity, :title, :description,
                    :evidence_data, :confidence_pct, :confidence_explanation, :required_checks,
                    :recommended_action, :status, :review_notes, :assigned_technician, :resolved_at
                );
            """, alert_data)
            conn.commit()
            return cursor.lastrowid

    def get_alerts(self, status: Optional[str] = None, category: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM alerts WHERE 1=1"
            params = []
            if status and status != "ALL":
                query += " AND status = ?"
                params.append(status)
            if category and category != "ALL":
                query += " AND category = ?"
                params.append(category)
            query += " ORDER BY timestamp DESC LIMIT ?;"
            params.append(limit)
            cursor.execute(query, params)
            return [dict(r) for r in cursor.fetchall()]

    def update_alert_status(self, alert_id: int, status: str, notes: Optional[str] = None, technician: Optional[str] = None) -> None:
        with self.get_connection() as conn:
            resolved_at = datetime.now().isoformat() if status in ("RESOLVED", "FALSE_ALARM") else None
            conn.execute("""
                UPDATE alerts
                SET status = ?, 
                    review_notes = COALESCE(?, review_notes),
                    assigned_technician = COALESCE(?, assigned_technician),
                    resolved_at = CASE WHEN ? IS NOT NULL THEN ? ELSE resolved_at END
                WHERE alert_id = ?;
            """, (status, notes, technician, resolved_at, resolved_at, alert_id))
            conn.commit()

    # --- Predictive Maintenance ---

    def save_maintenance_record(self, record_data: Dict[str, Any]) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            now_str = datetime.now().isoformat()
            record_data["created_at"] = record_data.get("created_at") or now_str
            record_data["updated_at"] = now_str
            cursor.execute("""
                INSERT INTO maintenance_records (
                    segment_id, priority_score, priority_category, estimated_condition,
                    contributing_reasons, recommended_action, status, assigned_to,
                    scheduled_date, notes, created_at, updated_at
                ) VALUES (
                    :segment_id, :priority_score, :priority_category, :estimated_condition,
                    :contributing_reasons, :recommended_action, :status, :assigned_to,
                    :scheduled_date, :notes, :created_at, :updated_at
                );
            """, record_data)
            conn.commit()
            return cursor.lastrowid

    def update_maintenance_status(self, record_id: int, status: str, notes: Optional[str] = None, assigned_to: Optional[str] = None, scheduled_date: Optional[str] = None) -> None:
        with self.get_connection() as conn:
            now_str = datetime.now().isoformat()
            conn.execute("""
                UPDATE maintenance_records
                SET status = ?,
                    notes = COALESCE(?, notes),
                    assigned_to = COALESCE(?, assigned_to),
                    scheduled_date = COALESCE(?, scheduled_date),
                    updated_at = ?
                WHERE record_id = ?;
            """, (status, notes, assigned_to, scheduled_date, now_str, record_id))
            conn.commit()

    def get_maintenance_records(self, segment_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if segment_id:
                cursor.execute("SELECT * FROM maintenance_records WHERE segment_id = ? ORDER BY updated_at DESC;", (segment_id,))
            else:
                cursor.execute("SELECT * FROM maintenance_records ORDER BY updated_at DESC;")
            return [dict(r) for r in cursor.fetchall()]

    def insert_inspection_finding(self, finding: Dict[str, Any]) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO inspection_findings (
                    segment_id, inspection_date, inspector_name, physical_condition_observed,
                    leak_detected, soil_moisture_level, ground_movement_signs,
                    cathodic_protection_status, actions_taken, recommendations
                ) VALUES (
                    :segment_id, :inspection_date, :inspector_name, :physical_condition_observed,
                    :leak_detected, :soil_moisture_level, :ground_movement_signs,
                    :cathodic_protection_status, :actions_taken, :recommendations
                );
            """, finding)
            conn.commit()
            return cursor.lastrowid

    def get_inspection_findings(self, segment_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if segment_id:
                cursor.execute("SELECT * FROM inspection_findings WHERE segment_id = ? ORDER BY inspection_date DESC;", (segment_id,))
            else:
                cursor.execute("SELECT * FROM inspection_findings ORDER BY inspection_date DESC;")
            return [dict(r) for r in cursor.fetchall()]

    # --- Reset & Demo Seed ---

    def reset_database(self) -> None:
        """Clears readings, alerts, maintenance and re-seeds clean default assets."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sensor_readings;")
            cursor.execute("DELETE FROM alerts;")
            cursor.execute("DELETE FROM maintenance_records;")
            cursor.execute("DELETE FROM inspection_findings;")
            cursor.execute("DELETE FROM pipeline_segments;")
            cursor.execute("DELETE FROM monitoring_stations;")
            cursor.execute("DELETE FROM treatment_plants;")
            cursor.execute("DELETE FROM water_sources;")
            cursor.execute("DELETE FROM reservoirs;")
            conn.commit()
        self._seed_default_topology_if_empty()


# Global Singleton accessor
_db_instance: Optional[DatabaseManager] = None

def get_db() -> DatabaseManager:
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseManager()
    return _db_instance
