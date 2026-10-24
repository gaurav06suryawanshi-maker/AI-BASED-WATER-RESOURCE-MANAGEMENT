"""
Physics-Inspired Simulated Sensor Engine for WaterGuard AI
Simulates pressure, flow, acoustic/vibration, and reservoir telemetry with realistic diurnal patterns and hydraulic behavior.
"""
import math
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import numpy as np

import config
from models.sensor import SensorType, SensorHealthStatus, SensorReading


class SensorSimulator:
    """Generates synthetic telemetry for pipeline segments and monitoring stations."""

    def __init__(self, random_seed: Optional[int] = 42):
        if random_seed is not None:
            random.seed(random_seed)
            np.random.seed(random_seed)

    @staticmethod
    def get_diurnal_multiplier(dt: datetime) -> float:
        """Calculates standard municipal diurnal demand multiplier based on hour of day.
        Peaks at 08:00 (morning) and 19:30 (evening), lowest at 03:00 (night minimum).
        """
        hour = dt.hour + dt.minute / 60.0
        # Diurnal curve modeled via combination of sinusoids
        base = 0.85
        morning_peak = 0.40 * math.exp(-0.5 * ((hour - 8.0) / 1.8) ** 2)
        evening_peak = 0.35 * math.exp(-0.5 * ((hour - 19.5) / 2.2) ** 2)
        night_dip = -0.25 * math.exp(-0.5 * ((hour - 3.5) / 2.0) ** 2)
        return max(0.45, min(1.45, base + morning_peak + evening_peak + night_dip))

    def generate_reading(
        self,
        dt: datetime,
        station_id: str,
        segment_id: str,
        sensor_type: str,
        nominal_value: float,
        unit: str,
        health: str = SensorHealthStatus.HEALTHY.value,
        anomaly_offset: float = 0.0,
        noise_std: float = 0.02,
        flag_notes: Optional[str] = None,
    ) -> SensorReading:
        """Generates an individual sensor reading respecting health status and anomaly offsets."""
        ts_str = dt.strftime("%Y-%m-%d %H:%M:%S")

        # Handle sensor faults
        if health == SensorHealthStatus.MISSING.value:
            return SensorReading(
                timestamp=ts_str,
                station_id=station_id,
                segment_id=segment_id,
                sensor_type=sensor_type,
                value=None,
                unit=unit,
                health_status=SensorHealthStatus.MISSING.value,
                is_synthetic=True,
                flag_notes=flag_notes or "Telemetry packet lost / timeout",
            )

        if health == SensorHealthStatus.FROZEN.value:
            # Statically fixed at nominal without any noise
            return SensorReading(
                timestamp=ts_str,
                station_id=station_id,
                segment_id=segment_id,
                sensor_type=sensor_type,
                value=round(nominal_value, 2),
                unit=unit,
                health_status=SensorHealthStatus.FROZEN.value,
                is_synthetic=True,
                flag_notes=flag_notes or "Sensor output frozen / ADC stalled",
            )

        if health == SensorHealthStatus.UNREALISTIC.value:
            # Physically impossible value
            unrealistic_val = -2.5 if sensor_type == SensorType.PRESSURE.value else 9999.0
            return SensorReading(
                timestamp=ts_str,
                station_id=station_id,
                segment_id=segment_id,
                sensor_type=sensor_type,
                value=unrealistic_val,
                unit=unit,
                health_status=SensorHealthStatus.UNREALISTIC.value,
                is_synthetic=True,
                flag_notes=flag_notes or "Physical range violation detected",
            )

        if health == SensorHealthStatus.DELAYED.value:
            # Timestamp delayed by 2 hours
            delayed_dt = dt - timedelta(hours=2)
            ts_str = delayed_dt.strftime("%Y-%m-%d %H:%M:%S")

        # Calculate standard value with noise and anomaly offset
        std_val = nominal_value * noise_std
        noise = random.gauss(0, max(0.01, std_val))
        if health == SensorHealthStatus.DEGRADED.value:
            noise *= 4.0  # Excessive jitter / drift

        calculated_val = max(0.0, nominal_value + anomaly_offset + noise)

        return SensorReading(
            timestamp=ts_str,
            station_id=station_id,
            segment_id=segment_id,
            sensor_type=sensor_type,
            value=round(calculated_val, 2),
            unit=unit,
            health_status=health,
            is_synthetic=True,
            flag_notes=flag_notes,
        )

    def generate_segment_snapshot(
        self,
        dt: datetime,
        segment: Dict[str, Any],
        scenario_overrides: Optional[Dict[str, Any]] = None,
    ) -> List[SensorReading]:
        """Generates all 4 sensor readings for a segment at a given timestamp."""
        seg_id = segment["segment_id"]
        overrides = scenario_overrides.get(seg_id, {}) if scenario_overrides else {}

        diurnal = self.get_diurnal_multiplier(dt)
        base_flow = segment["nominal_flow_m3h"] * diurnal
        base_pressure = segment["nominal_pressure_bar"]

        # Acoustic baseline: 12-20 index with slight flow correlation
        base_acoustic = 14.0 + (base_flow / segment["nominal_flow_m3h"]) * 6.0
        base_vibration = 0.9 + (base_flow / segment["nominal_flow_m3h"]) * 0.4

        # Apply overrides if specified
        flow_offset = overrides.get("flow_offset", 0.0)
        pressure_offset = overrides.get("pressure_offset", 0.0)
        acoustic_offset = overrides.get("acoustic_offset", 0.0)
        vibration_offset = overrides.get("vibration_offset", 0.0)

        pressure_health = overrides.get("pressure_health", SensorHealthStatus.HEALTHY.value)
        flow_health = overrides.get("flow_health", SensorHealthStatus.HEALTHY.value)
        acoustic_health = overrides.get("acoustic_health", SensorHealthStatus.HEALTHY.value)

        readings = []

        # 1. Upstream Pressure
        readings.append(self.generate_reading(
            dt=dt,
            station_id=segment["upstream_station_id"],
            segment_id=seg_id,
            sensor_type=SensorType.PRESSURE.value,
            nominal_value=base_pressure,
            unit=config.UNITS["pressure"],
            health=pressure_health,
            anomaly_offset=pressure_offset,
            noise_std=0.015,
            flag_notes=overrides.get("pressure_notes"),
        ))

        # 2. Inflow / Segment Flow Meter
        readings.append(self.generate_reading(
            dt=dt,
            station_id=segment["upstream_station_id"],
            segment_id=seg_id,
            sensor_type=SensorType.FLOW.value,
            nominal_value=base_flow,
            unit=config.UNITS["flow"],
            health=flow_health,
            anomaly_offset=flow_offset,
            noise_std=0.02,
            flag_notes=overrides.get("flow_notes"),
        ))

        # 3. Acoustic Sensor
        readings.append(self.generate_reading(
            dt=dt,
            station_id=segment["downstream_station_id"],
            segment_id=seg_id,
            sensor_type=SensorType.ACOUSTIC.value,
            nominal_value=base_acoustic,
            unit=config.UNITS["acoustic"],
            health=acoustic_health,
            anomaly_offset=acoustic_offset,
            noise_std=0.04,
            flag_notes=overrides.get("acoustic_notes"),
        ))

        # 4. Vibration Sensor
        readings.append(self.generate_reading(
            dt=dt,
            station_id=segment["downstream_station_id"],
            segment_id=seg_id,
            sensor_type=SensorType.VIBRATION.value,
            nominal_value=base_vibration,
            unit=config.UNITS["vibration"],
            health=acoustic_health,
            anomaly_offset=vibration_offset,
            noise_std=0.05,
            flag_notes=overrides.get("vibration_notes"),
        ))

        return readings

    def generate_reservoir_reading(
        self,
        dt: datetime,
        reservoir: Dict[str, Any],
        level_offset_pct: float = 0.0,
        health: str = SensorHealthStatus.HEALTHY.value,
    ) -> SensorReading:
        """Simulates reservoir level telemetry."""
        base_pct = reservoir["current_storage_pct"] + level_offset_pct
        base_pct = max(0.0, min(100.0, base_pct))
        max_level_m = reservoir["max_level_m"]
        calculated_level_m = (base_pct / 100.0) * max_level_m

        return self.generate_reading(
            dt=dt,
            station_id=reservoir["reservoir_id"],
            segment_id=reservoir["connected_segment_id"],
            sensor_type=SensorType.RESERVOIR_LEVEL.value,
            nominal_value=calculated_level_m,
            unit="m",
            health=health,
            anomaly_offset=0.0,
            noise_std=0.005,
            flag_notes="Low Reservoir Level" if base_pct < reservoir["low_level_threshold_pct"] else None,
        )

    def generate_historical_series(
        self,
        segments: List[Dict[str, Any]],
        reservoirs: List[Dict[str, Any]],
        hours_back: int = 24,
        interval_minutes: int = 30,
        scenario_overrides: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Generates historical time-series of sensor readings across the network."""
        now = datetime.now()
        readings_list: List[Dict[str, Any]] = []

        total_steps = int((hours_back * 60) / interval_minutes)

        for step in range(total_steps, -1, -1):
            t = now - timedelta(minutes=step * interval_minutes)

            # In the last 4 hours of history, apply scenario overrides if provided
            is_active_anomaly_time = (step * interval_minutes) <= 240
            current_overrides = scenario_overrides if is_active_anomaly_time else None

            for seg in segments:
                snapshot = self.generate_segment_snapshot(t, seg, current_overrides)
                for r in snapshot:
                    readings_list.append(r.to_dict())

            for res in reservoirs:
                res_health = SensorHealthStatus.HEALTHY.value
                r_reading = self.generate_reservoir_reading(t, res, health=res_health)
                readings_list.append(r_reading.to_dict())

        return readings_list
