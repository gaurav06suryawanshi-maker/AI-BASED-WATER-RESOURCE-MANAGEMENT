"""
Predictive Maintenance and Inspection Data Models
"""
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any


class MaintenanceStatus(str, Enum):
    PENDING = "Pending"
    UNDER_REVIEW = "Under Review"
    SCHEDULED = "Scheduled"
    COMPLETED = "Completed"


class AssetConditionGrade(str, Enum):
    GRADE_1_EXCELLENT = "Grade 1 - Very Good (Minor cosmetic wear)"
    GRADE_2_GOOD = "Grade 2 - Good (Expected aging, minor service)"
    GRADE_3_MODERATE = "Grade 3 - Moderate (Signs of deterioration, plan maintenance)"
    GRADE_4_POOR = "Grade 4 - Poor (Significant deterioration, inspection needed)"
    GRADE_5_VERY_POOR = "Grade 5 - Critical (Severe defect/failure risk, immediate intervention)"


@dataclass
class MaintenanceRecord:
    segment_id: str
    priority_score: float
    priority_category: str
    estimated_condition: str  # Note: Model-derived assessment, not physical inspection
    contributing_reasons: str
    recommended_action: str
    status: str = MaintenanceStatus.PENDING.value
    assigned_to: Optional[str] = None
    scheduled_date: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    record_id: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "segment_id": self.segment_id,
            "priority_score": self.priority_score,
            "priority_category": self.priority_category,
            "estimated_condition": self.estimated_condition,
            "contributing_reasons": self.contributing_reasons,
            "recommended_action": self.recommended_action,
            "status": self.status,
            "assigned_to": self.assigned_to,
            "scheduled_date": self.scheduled_date,
            "notes": self.notes,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class InspectionFinding:
    segment_id: str
    inspection_date: str
    inspector_name: str
    physical_condition_observed: str
    leak_detected: bool
    soil_moisture_level: str  # Dry, Damp, Waterlogged
    ground_movement_signs: bool
    cathodic_protection_status: str  # Good, Degraded, Absent
    actions_taken: str
    recommendations: str
    finding_id: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "segment_id": self.segment_id,
            "inspection_date": self.inspection_date,
            "inspector_name": self.inspector_name,
            "physical_condition_observed": self.physical_condition_observed,
            "leak_detected": 1 if self.leak_detected else 0,
            "soil_moisture_level": self.soil_moisture_level,
            "ground_movement_signs": 1 if self.ground_movement_signs else 0,
            "cathodic_protection_status": self.cathodic_protection_status,
            "actions_taken": self.actions_taken,
            "recommendations": self.recommendations,
        }
