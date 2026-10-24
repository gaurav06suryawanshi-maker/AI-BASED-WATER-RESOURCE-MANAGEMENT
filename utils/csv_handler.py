"""
CSV Data Validation, Import, and Export Handlers
Ensures user-imported CSV files adhere to strict schema and validation constraints.
"""
import io
from typing import Dict, Any, List, Tuple, Optional
import pandas as pd
from datetime import datetime
import config


class CSVHandler:
    REQUIRED_ASSET_COLUMNS = [
        "segment_id", "name", "stage", "upstream_station_id", "downstream_station_id",
        "length_km", "diameter_mm", "material", "installation_year",
        "nominal_pressure_bar", "nominal_flow_m3h", "criticality"
    ]

    REQUIRED_READING_COLUMNS = [
        "timestamp", "station_id", "segment_id", "sensor_type", "value", "unit", "health_status"
    ]

    REQUIRED_MAINTENANCE_COLUMNS = [
        "segment_id", "inspection_date", "inspector_name", "physical_condition_observed",
        "leak_detected", "soil_moisture_level", "ground_movement_signs",
        "cathodic_protection_status", "actions_taken", "recommendations"
    ]

    @classmethod
    def validate_and_parse_assets(cls, file_content: Any) -> Tuple[bool, Optional[pd.DataFrame], List[str]]:
        """Validates uploaded pipeline asset CSV data."""
        errors = []
        try:
            if isinstance(file_content, bytes):
                df = pd.read_csv(io.BytesIO(file_content))
            elif isinstance(file_content, str):
                df = pd.read_csv(io.StringIO(file_content))
            else:
                df = pd.read_csv(file_content)
        except Exception as e:
            return False, None, [f"Failed to parse CSV file: {str(e)}"]

        # Column existence check
        missing_cols = [col for col in cls.REQUIRED_ASSET_COLUMNS if col not in df.columns]
        if missing_cols:
            errors.append(f"Missing required columns: {', '.join(missing_cols)}")

        if errors:
            return False, None, errors

        # Data type and value range validation
        for idx, row in df.iterrows():
            row_num = idx + 2
            if pd.isna(row["segment_id"]) or str(row["segment_id"]).strip() == "":
                errors.append(f"Row {row_num}: segment_id cannot be blank")

            try:
                length = float(row["length_km"])
                if length <= 0.0 or length > 500.0:
                    errors.append(f"Row {row_num}: length_km must be between 0.1 and 500 km (got {length})")
            except (ValueError, TypeError):
                errors.append(f"Row {row_num}: length_km must be a numeric value")

            try:
                diam = int(row["diameter_mm"])
                if diam < 50 or diam > 3000:
                    errors.append(f"Row {row_num}: diameter_mm must be between 50 and 3000 mm (got {diam})")
            except (ValueError, TypeError):
                errors.append(f"Row {row_num}: diameter_mm must be an integer")

            try:
                year = int(row["installation_year"])
                current_year = datetime.now().year
                if year < 1850 or year > current_year:
                    errors.append(f"Row {row_num}: installation_year must be between 1850 and {current_year}")
            except (ValueError, TypeError):
                errors.append(f"Row {row_num}: installation_year must be a valid year")

            if len(errors) > 15:
                errors.append("Too many validation errors; aborting further row inspection.")
                break

        if errors:
            return False, None, errors

        # Fill optional columns with defaults if missing
        if "soil_condition" not in df.columns:
            df["soil_condition"] = "Moderate"
        if "burial_depth_m" not in df.columns:
            df["burial_depth_m"] = 1.5
        if "past_repair_count" not in df.columns:
            df["past_repair_count"] = 0
        if "last_inspection_date" not in df.columns:
            df["last_inspection_date"] = None
        if "nearby_excavation_risk" not in df.columns:
            df["nearby_excavation_risk"] = 0
        if "connected_reservoir_id" not in df.columns:
            df["connected_reservoir_id"] = None

        return True, df, []

    @classmethod
    def validate_and_parse_readings(cls, file_content: Any) -> Tuple[bool, Optional[pd.DataFrame], List[str]]:
        """Validates uploaded sensor reading CSV data."""
        errors = []
        try:
            if isinstance(file_content, bytes):
                df = pd.read_csv(io.BytesIO(file_content))
            elif isinstance(file_content, str):
                df = pd.read_csv(io.StringIO(file_content))
            else:
                df = pd.read_csv(file_content)
        except Exception as e:
            return False, None, [f"Failed to parse CSV file: {str(e)}"]

        missing_cols = [col for col in cls.REQUIRED_READING_COLUMNS if col not in df.columns]
        if missing_cols:
            errors.append(f"Missing required columns: {', '.join(missing_cols)}")

        if errors:
            return False, None, errors

        valid_types = {"PRESSURE", "FLOW", "ACOUSTIC", "VIBRATION", "RESERVOIR_LEVEL"}
        valid_health = {"HEALTHY", "DEGRADED", "FROZEN", "MISSING", "DELAYED", "UNREALISTIC"}

        for idx, row in df.head(100).iterrows():
            row_num = idx + 2
            s_type = str(row["sensor_type"]).upper().strip()
            if s_type not in valid_types:
                errors.append(f"Row {row_num}: Unknown sensor_type '{row['sensor_type']}'. Must be one of {valid_types}")

            health = str(row["health_status"]).upper().strip()
            if health not in valid_health:
                errors.append(f"Row {row_num}: Unknown health_status '{row['health_status']}'. Must be one of {valid_health}")

            # Check timestamp format
            ts_str = str(row["timestamp"]).strip()
            try:
                datetime.fromisoformat(ts_str.replace(" ", "T"))
            except ValueError:
                errors.append(f"Row {row_num}: timestamp '{ts_str}' must be ISO-8601 (YYYY-MM-DD HH:MM:SS)")

            if len(errors) > 10:
                errors.append("Sample validation threshold reached with multiple errors.")
                break

        if errors:
            return False, None, errors

        if "is_synthetic" not in df.columns:
            df["is_synthetic"] = 0  # Imported readings default to external source
        if "flag_notes" not in df.columns:
            df["flag_notes"] = None

        return True, df, []

    @classmethod
    def get_sample_assets_csv(cls) -> str:
        """Returns sample CSV template for pipeline assets."""
        return (
            "segment_id,name,stage,upstream_station_id,downstream_station_id,length_km,diameter_mm,material,installation_year,nominal_pressure_bar,nominal_flow_m3h,criticality,soil_condition,burial_depth_m,past_repair_count,last_inspection_date,nearby_excavation_risk,connected_reservoir_id\n"
            "TX-100,Raw Water Intake Line,Intake,MS-01,MS-02,4.2,1000,Steel,2012,4.2,2500.0,Critical,Moderate,2.2,0,2025-08-14,0,\n"
            "TX-101,Main High-Pressure Transmission Trunk,Transmission,MS-02,MS-03,6.8,900,Ductile Iron,2005,5.8,2400.0,Critical,Moderate,2.0,1,2025-11-02,0,\n"
            "TX-102,North Reservoir Feeder Main,Transmission,MS-03,MS-04,5.1,750,Ductile Iron,2008,4.8,1150.0,High,Non-corrosive,1.8,0,2026-02-19,0,RES-NORTH\n"
            "TX-103,South Valley Transmission Aqueduct,Transmission,MS-03,MS-05,8.4,800,Prestressed Concrete,1994,5.2,1250.0,Critical,Corrosive,2.1,3,2025-04-10,1,RES-SOUTH\n"
            "DN-201,Metro East Residential Sector Feeder,Distribution,MS-04,MS-06,3.6,500,HDPE,2018,3.8,620.0,Medium,Non-corrosive,1.4,0,2026-05-12,0,\n"
            "DN-202,Commercial District Metered Area,Distribution,MS-06,MS-07,2.9,400,Ductile Iron,2010,3.6,480.0,High,Moderate,1.5,1,2025-09-30,0,\n"
            "DN-203,Industrial Zone Heavy Flow Loop,Distribution,MS-05,MS-08,4.5,600,Steel,2002,4.1,720.0,High,Corrosive,1.6,2,2025-07-21,0,\n"
            "DN-204,Old Quarter Heritage Reticulation,Distribution,MS-07,MS-09,3.2,300,Cast Iron,1978,3.2,280.0,Critical,Corrosive,1.2,5,2024-10-15,1,\n"
        )

    @classmethod
    def get_sample_readings_csv(cls) -> str:
        """Returns sample CSV template for sensor telemetry."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return (
            "timestamp,station_id,segment_id,sensor_type,value,unit,health_status,is_synthetic,flag_notes\n"
            f"{now},MS-02,TX-101,PRESSURE,5.82,bar,HEALTHY,1,Nominal pump discharge\n"
            f"{now},MS-02,TX-101,FLOW,2410.5,m³/h,HEALTHY,1,Bulk flow meter\n"
            f"{now},MS-03,TX-101,ACOUSTIC,16.4,Index (0-100),HEALTHY,1,Background noise\n"
            f"{now},MS-03,TX-101,VIBRATION,1.15,mm/s,HEALTHY,1,Baseline pipe vibration\n"
            f"{now},MS-07,DN-204,PRESSURE,2.55,bar,HEALTHY,1,Depressed heritage line\n"
            f"{now},MS-07,DN-204,FLOW,318.2,m³/h,HEALTHY,1,Excessive flow rate\n"
            f"{now},MS-09,DN-204,ACOUSTIC,62.8,Index (0-100),HEALTHY,1,Elevated acoustic hiss\n"
        )
