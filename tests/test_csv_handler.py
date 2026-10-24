"""
Tests for CSV schema validation, parsing, and export handlers
"""
import pytest
from utils.csv_handler import CSVHandler


def test_valid_assets_csv_parsing():
    valid_csv = CSVHandler.get_sample_assets_csv()
    is_valid, df, errors = CSVHandler.validate_and_parse_assets(valid_csv)
    assert is_valid is True
    assert df is not None
    assert len(errors) == 0
    assert len(df) >= 8
    assert "TX-101" in df["segment_id"].values


def test_invalid_assets_csv_missing_columns():
    invalid_csv = "segment_id,name\nTX-1,Main"
    is_valid, df, errors = CSVHandler.validate_and_parse_assets(invalid_csv)
    assert is_valid is False
    assert df is None
    assert any("Missing required columns" in err for err in errors)


def test_invalid_assets_csv_bad_data_types():
    bad_data = (
        "segment_id,name,stage,upstream_station_id,downstream_station_id,length_km,diameter_mm,material,installation_year,nominal_pressure_bar,nominal_flow_m3h,criticality\n"
        "TX-1,Test,Transmission,MS-1,MS-2,NOT_A_FLOAT,800,Steel,2010,5.0,1000.0,Critical\n"
    )
    is_valid, df, errors = CSVHandler.validate_and_parse_assets(bad_data)
    assert is_valid is False
    assert any("numeric value" in err for err in errors)


def test_valid_readings_csv_parsing():
    sample_readings = CSVHandler.get_sample_readings_csv()
    is_valid, df, errors = CSVHandler.validate_and_parse_readings(sample_readings)
    assert is_valid is True
    assert df is not None
    assert len(errors) == 0
    assert len(df) >= 7


def test_invalid_readings_csv_bad_sensor_type():
    bad_readings = (
        "timestamp,station_id,segment_id,sensor_type,value,unit,health_status\n"
        "2026-10-24 10:00:00,MS-1,TX-1,QUANTUM_SPIN,4.5,bar,HEALTHY\n"
    )
    is_valid, df, errors = CSVHandler.validate_and_parse_readings(bad_readings)
    assert is_valid is False
    assert any("Unknown sensor_type" in err for err in errors)
