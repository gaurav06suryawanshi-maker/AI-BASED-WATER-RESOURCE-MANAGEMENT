"""
Sensor readings and health status data models
"""
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any


class SensorType(str, Enum):
    PRESSURE = "PRESSURE"
    FLOW = "FLOW"
    ACOUSTIC = "ACOUSTIC"
    VIBRATION = "VIBRATION"
    RESERVOIR_LEVEL = "RESERVOIR_LEVEL"


class SensorHealthStatus(str, Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    FROZEN = "FROZEN"
    MISSING = "MISSING"
    DELAYED = "DELAYED"
    UNREALISTIC = "UNREALISTIC"


@dataclass
class SensorReading:
    timestamp: str  # ISO-8601 string YYYY-MM-DD HH:MM:SS
    station_id: str
    segment_id: str
    sensor_type: str
    value: Optional[float]
    unit: str
    health_status: str = SensorHealthStatus.HEALTHY.value
    is_synthetic: bool = True
    flag_notes: Optional[str] = None
    reading_id: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reading_id": self.reading_id,
            "timestamp": self.timestamp,
            "station_id": self.station_id,
            "segment_id": self.segment_id,
            "sensor_type": self.sensor_type,
            "value": self.value,
            "unit": self.unit,
            "health_status": self.health_status,
            "is_synthetic": 1 if self.is_synthetic else 0,
            "flag_notes": self.flag_notes,
        }
