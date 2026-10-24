"""
Sensor Data Quality Filter
Validates telemetry integrity before algorithmic analysis.
Disqualifies or flags corrupted, missing, frozen, delayed, and physically unrealistic readings
to eliminate false positives in hydraulic and leak detection engines.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
import numpy as np

import config
from models.sensor import SensorType, SensorHealthStatus


@dataclass
class DataQualityReport:
    segment_id: str
    is_valid_for_analysis: bool
    data_quality_score: float  # 0 to 100
    overall_health: str
    sensor_issues: List[str] = field(default_factory=list)
    frozen_sensors: List[str] = field(default_factory=list)
    missing_sensors: List[str] = field(default_factory=list)
    unrealistic_sensors: List[str] = field(default_factory=list)
    delayed_sensors: List[str] = field(default_factory=list)
    recommended_action: Optional[str] = None


class SensorQualityFilter:
    """Pre-processing validation filter that isolates sensor faults from physical water infrastructure anomalies."""

    @staticmethod
    def validate_single_reading(reading: Dict[str, Any]) -> Dict[str, Any]:
        """Validates a single telemetry reading against strict physical bounds."""
        val = reading.get("value")
        s_type = reading.get("sensor_type")
        issues = []
        inferred_health = reading.get("health_status", SensorHealthStatus.HEALTHY.value)

        # 1. Missing / None check
        if val is None or (isinstance(val, float) and np.isnan(val)):
            return {
                "is_valid": False,
                "inferred_health": SensorHealthStatus.MISSING.value,
                "issue": "Reading value is missing or NaN",
            }

        # 2. Physical range bounds checks
        if s_type == SensorType.PRESSURE.value:
            if val < config.THRESHOLDS["pressure_physical_min"]:
                issues.append(f"Physical impossibility: Negative pressure ({val} bar)")
                inferred_health = SensorHealthStatus.UNREALISTIC.value
            elif val > config.THRESHOLDS["pressure_physical_max"]:
                issues.append(f"Exceeds max PN16 structural rating ({val} bar > {config.THRESHOLDS['pressure_physical_max']} bar)")
                inferred_health = SensorHealthStatus.UNREALISTIC.value

        elif s_type == SensorType.FLOW.value:
            if val < config.THRESHOLDS["flow_physical_min"]:
                issues.append(f"Physical impossibility: Negative flow meter value ({val} m³/h)")
                inferred_health = SensorHealthStatus.UNREALISTIC.value
            elif val > config.THRESHOLDS["flow_physical_max"]:
                issues.append(f"Exceeds maximum transmission flow capability ({val} m³/h)")
                inferred_health = SensorHealthStatus.UNREALISTIC.value

        elif s_type == SensorType.ACOUSTIC.value:
            if val < 0.0 or val > 100.0:
                issues.append(f"Acoustic index out of calibrated bounds 0-100 ({val})")
                inferred_health = SensorHealthStatus.UNREALISTIC.value

        # 3. Explicit health status pass-through
        if reading.get("health_status") in (
            SensorHealthStatus.FROZEN.value,
            SensorHealthStatus.DELAYED.value,
            SensorHealthStatus.DEGRADED.value,
            SensorHealthStatus.MISSING.value,
            SensorHealthStatus.UNREALISTIC.value,
        ):
            inferred_health = reading["health_status"]

        is_valid = (inferred_health == SensorHealthStatus.HEALTHY.value) or (inferred_health == SensorHealthStatus.DEGRADED.value)

        return {
            "is_valid": is_valid,
            "inferred_health": inferred_health,
            "issue": "; ".join(issues) if issues else None,
        }

    @staticmethod
    def evaluate_recent_stream(segment_id: str, readings_by_type: Dict[str, List[Dict[str, Any]]]) -> DataQualityReport:
        """Analyzes a recent window of readings per sensor type on a pipeline segment
        to detect stuck ADC values (frozen), packet dropouts, or calibration drift.
        """
        sensor_issues = []
        frozen = []
        missing = []
        unrealistic = []
        delayed = []

        total_checked = 0
        penalty = 0.0

        for s_type, readings in readings_by_type.items():
            if not readings:
                missing.append(s_type)
                sensor_issues.append(f"{s_type}: No telemetry available (Missing)")
                penalty += 35.0
                continue

            values = [r.get("value") for r in readings if r.get("value") is not None]
            total_checked += 1

            # Missing check
            if len(values) < len(readings) * 0.5:
                missing.append(s_type)
                sensor_issues.append(f"{s_type}: >50% packet dropouts")
                penalty += 30.0

            # Frozen sensor check: 4 or more identical readings
            if len(values) >= config.THRESHOLDS["max_frozen_consecutive_readings"]:
                recent_sub = values[:config.THRESHOLDS["max_frozen_consecutive_readings"]]
                if np.std(recent_sub) < 1e-6:
                    frozen.append(s_type)
                    sensor_issues.append(f"{s_type}: Flatline/Frozen output detected ({recent_sub[0]})")
                    penalty += 35.0

            # Check individual readings
            for r in readings[:3]:  # Check latest 3 readings
                val_res = SensorQualityFilter.validate_single_reading(r)
                if val_res["inferred_health"] == SensorHealthStatus.UNREALISTIC.value:
                    if s_type not in unrealistic:
                        unrealistic.append(s_type)
                        sensor_issues.append(f"{s_type}: Unrealistic values ({val_res['issue']})")
                        penalty += 40.0
                elif val_res["inferred_health"] == SensorHealthStatus.DELAYED.value:
                    if s_type not in delayed:
                        delayed.append(s_type)
                        sensor_issues.append(f"{s_type}: Delayed telemetry arrival")
                        penalty += 15.0

        quality_score = max(0.0, round(100.0 - penalty, 1))
        is_valid = (quality_score >= 50.0) and (len(unrealistic) == 0) and (len(frozen) == 0)

        overall_health = SensorHealthStatus.HEALTHY.value
        if unrealistic:
            overall_health = SensorHealthStatus.UNREALISTIC.value
        elif frozen:
            overall_health = SensorHealthStatus.FROZEN.value
        elif missing:
            overall_health = SensorHealthStatus.MISSING.value
        elif delayed:
            overall_health = SensorHealthStatus.DELAYED.value
        elif quality_score < 75.0:
            overall_health = SensorHealthStatus.DEGRADED.value

        action = None
        if not is_valid:
            action = f"Telemetry hardware inspection required for {segment_id}. Recalibrate or replace flagged sensors ({', '.join(sensor_issues)}) before trusting anomaly alarms."

        return DataQualityReport(
            segment_id=segment_id,
            is_valid_for_analysis=is_valid,
            data_quality_score=quality_score,
            overall_health=overall_health,
            sensor_issues=sensor_issues,
            frozen_sensors=frozen,
            missing_sensors=missing,
            unrealistic_sensors=unrealistic,
            delayed_sensors=delayed,
            recommended_action=action,
        )
