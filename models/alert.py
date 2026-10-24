"""
Alerts, Incidents, and Detection Record Data Models
"""
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any


class AlertSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AlertCategory(str, Enum):
    SUSPECTED_LEAK = "SUSPECTED_LEAK"
    SUDDEN_BURST = "SUDDEN_BURST"
    PRESSURE_ANOMALY = "PRESSURE_ANOMALY"
    SENSOR_FAULT = "SENSOR_FAULT"
    RESERVOIR_WARNING = "RESERVOIR_WARNING"
    MAINTENANCE_RISK = "MAINTENANCE_RISK"


class IncidentStatus(str, Enum):
    ACTIVE = "ACTIVE"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED = "RESOLVED"
    FALSE_ALARM = "FALSE_ALARM"


@dataclass
class Alert:
    timestamp: str
    segment_id: str
    category: str
    severity: str
    title: str
    description: str
    evidence_data: str  # JSON string or descriptive summary
    confidence_pct: float
    confidence_explanation: str
    required_checks: str
    recommended_action: str
    status: str = IncidentStatus.ACTIVE.value
    review_notes: Optional[str] = None
    assigned_technician: Optional[str] = None
    resolved_at: Optional[str] = None
    alert_id: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "timestamp": self.timestamp,
            "segment_id": self.segment_id,
            "category": self.category,
            "severity": self.severity,
            "title": self.title,
            "description": self.description,
            "evidence_data": self.evidence_data,
            "confidence_pct": self.confidence_pct,
            "confidence_explanation": self.confidence_explanation,
            "required_checks": self.required_checks,
            "recommended_action": self.recommended_action,
            "status": self.status,
            "review_notes": self.review_notes,
            "assigned_technician": self.assigned_technician,
            "resolved_at": self.resolved_at,
        }
