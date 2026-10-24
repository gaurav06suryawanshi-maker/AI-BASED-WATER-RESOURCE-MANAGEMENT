"""
Explainable Risk and Pipeline Inspection Priority Scoring Engine
Calculates a 0-100 inspection priority index by combining immediate sensor telemetry anomalies
with long-term physical asset deterioration factors.
Explicitly discloses that scores are advisory decision-support indexes rather than proven failure probabilities.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

import config
from risk.recommendations import RecommendationGenerator


@dataclass
class RiskAssessmentResult:
    segment_id: str
    priority_score: float  # 0 to 100
    priority_category: str  # NORMAL, MONITOR, INSPECTION_RECOMMENDED, URGENT_REVIEW, INSUFFICIENT_DATA
    badge_label: str
    badge_color: str
    immediate_anomaly_score: float  # Subtotal (max 55)
    long_term_asset_score: float    # Subtotal (max 45)
    estimated_condition_grade: str  # Grade 1 to Grade 5
    factor_breakdown: Dict[str, float]
    contributing_reasons: List[str]
    recommended_response: str
    data_quality_valid: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "segment_id": self.segment_id,
            "priority_score": self.priority_score,
            "priority_category": self.priority_category,
            "badge_label": self.badge_label,
            "badge_color": self.badge_color,
            "immediate_anomaly_score": self.immediate_anomaly_score,
            "long_term_asset_score": self.long_term_asset_score,
            "estimated_condition_grade": self.estimated_condition_grade,
            "factor_breakdown": self.factor_breakdown,
            "contributing_reasons": self.contributing_reasons,
            "recommended_response": self.recommended_response,
            "data_quality_valid": self.data_quality_valid,
        }


class RiskScoringEngine:
    """Computes an explainable, multi-factor inspection priority index."""

    @staticmethod
    def calculate_asset_vulnerability_score(segment: Dict[str, Any]) -> Tuple[float, Dict[str, float], List[str]]:
        """Calculates long-term physical asset vulnerability score (max 45 points).
        Factors:
        - Age & Material (max 20 pts)
        - Incident & Repair History (max 15 pts)
        - Supply Criticality & Soil/Excavation (max 10 pts)
        """
        reasons = []
        breakdown = {}

        material = segment.get("material", "Ductile Iron")
        current_year = datetime.now().year
        install_year = segment.get("installation_year", current_year - 15)
        age = max(0, current_year - install_year)

        # 1. Material and Age Vulnerability (Max 20 pts)
        mat_pts = 0.0
        if material == "Cast Iron":
            # Cast iron suffers from graphitic corrosion and brittleness
            mat_pts = min(20.0, 10.0 + (age * 0.25))
            reasons.append(f"Legacy Cast Iron material ({age} yrs old, susceptible to graphitization): +{mat_pts:.1f} pts")
        elif material in ("Prestressed Concrete", "Asbestos-Cement"):
            mat_pts = min(20.0, 8.0 + (age * 0.22))
            reasons.append(f"{material} construction ({age} yrs old, prone to wire corrosion/spalling): +{mat_pts:.1f} pts")
        elif material == "Steel":
            soil = segment.get("soil_condition", "Moderate")
            soil_factor = 4.0 if soil == "Corrosive" else 1.0
            mat_pts = min(20.0, 5.0 + (age * 0.18) + soil_factor)
            reasons.append(f"Steel pipeline in {soil} soil ({age} yrs old): +{mat_pts:.1f} pts")
        elif material == "Ductile Iron":
            mat_pts = min(20.0, 3.0 + (age * 0.15))
            reasons.append(f"Ductile Iron ({age} yrs old): +{mat_pts:.1f} pts")
        else:  # HDPE / PVC
            mat_pts = min(20.0, 1.0 + (age * 0.08))
            reasons.append(f"Modern corrosion-resistant {material} ({age} yrs old): +{mat_pts:.1f} pts")

        mat_pts = round(min(20.0, mat_pts), 1)
        breakdown["asset_age_material"] = mat_pts

        # 2. Repair and Failure History (Max 15 pts)
        repairs = segment.get("past_repair_count", 0)
        rep_pts = 0.0
        if repairs >= 4:
            rep_pts = 15.0
            reasons.append(f"High historical repeat failure count ({repairs} past repairs recorded): +15.0 pts")
        elif repairs >= 2:
            rep_pts = 10.0
            reasons.append(f"Moderate failure history ({repairs} past repairs recorded): +10.0 pts")
        elif repairs == 1:
            rep_pts = 5.0
            reasons.append(f"Isolated past repair recorded on segment: +5.0 pts")
        else:
            reasons.append("Clean asset history with zero recorded failures: +0.0 pts")

        breakdown["incident_history"] = rep_pts

        # 3. Criticality and Consequence (Max 10 pts)
        crit = segment.get("criticality", "Medium")
        crit_pts = 0.0
        if crit == "Critical":
            crit_pts = 7.0
            reasons.append("Critical transmission main / high supply consequence tier: +7.0 pts")
        elif crit == "High":
            crit_pts = 5.0
            reasons.append("High priority feeder: +5.0 pts")
        elif crit == "Medium":
            crit_pts = 3.0
        else:
            crit_pts = 1.0

        # Nearby excavation bonus
        if segment.get("nearby_excavation_risk"):
            crit_pts += 3.0
            reasons.append("Third-party civil excavation activity flagged in pipeline easement: +3.0 pts")

        crit_pts = round(min(10.0, crit_pts), 1)
        breakdown["criticality_consequence"] = crit_pts

        long_term_total = round(mat_pts + rep_pts + crit_pts, 1)
        return long_term_total, breakdown, reasons

    @classmethod
    def evaluate_segment_risk(
        cls,
        segment: Dict[str, Any],
        detection_context: Optional[Dict[str, Any]] = None,
    ) -> RiskAssessmentResult:
        """Synthesizes physical asset factors and active telemetry conditions into final inspection priority."""
        seg_id = segment["segment_id"]
        ctx = detection_context or {}

        # 1. Long-Term Asset Subtotal (0 to 45 pts)
        long_term_score, breakdown, reasons = cls.calculate_asset_vulnerability_score(segment)

        # 2. Immediate Active Telemetry Subtotal (0 to 55 pts)
        immediate_score = 0.0
        active_hydraulic_pts = 0.0
        acoustic_pts = 0.0

        has_burst = False
        has_leak = False
        has_surge = False
        has_sensor_fault = False

        quality_report = ctx.get("quality_report")
        if quality_report and not quality_report.is_valid_for_analysis:
            has_sensor_fault = True
            reasons.append(f"Telemetry Hardware Fault: {'; '.join(quality_report.sensor_issues)}")

        water_balance = ctx.get("water_balance")
        hydraulic = ctx.get("hydraulic")
        acoustic = ctx.get("acoustic")
        diag = ctx.get("diagnosis", "NORMAL")

        if diag == "SUDDEN_BURST":
            has_burst = True
            active_hydraulic_pts = 35.0
            acoustic_pts = 20.0
            reasons.append("Severe active hydraulic burst collapse: +35.0 pts")
            reasons.append("Violent acoustic/vibration cavitation: +20.0 pts")

        elif diag == "SUSPECTED_LEAK":
            has_leak = True
            active_hydraulic_pts = 25.0
            acoustic_pts = 15.0
            reasons.append(f"Active unexplained volumetric deficit ({water_balance.unexplained_discrepancy_m3h:.1f} m³/h): +25.0 pts")
            reasons.append(f"Elevated acoustic pipe-wall vibration ({acoustic.acoustic_index:.1f}/100): +15.0 pts")

        elif diag == "PRESSURE_ANOMALY":
            has_surge = True
            active_hydraulic_pts = 16.0
            acoustic_pts = 0.0
            reasons.append(f"Severe transient pressure surge (+{hydraulic.pressure_delta_bar:.2f} bar): +16.0 pts")

        elif diag == "UNRECONCILED_FLOW":
            active_hydraulic_pts = 12.0
            reasons.append(f"Unconfirmed flow deficit ({water_balance.unexplained_discrepancy_m3h:.1f} m³/h, quiet acoustics): +12.0 pts")

        else:
            # Baseline quiet
            reasons.append("Current hydraulic and acoustic readings are within normal nominal bounds: +0.0 pts")

        active_hydraulic_pts = min(35.0, active_hydraulic_pts)
        acoustic_pts = min(20.0, acoustic_pts)
        immediate_score = round(active_hydraulic_pts + acoustic_pts, 1)

        breakdown["active_hydraulic_imbalance"] = active_hydraulic_pts
        breakdown["acoustic_evidence"] = acoustic_pts

        # Total Priority Score
        total_score = round(min(100.0, long_term_score + immediate_score), 1)

        # In case of an active catastrophic burst, floor the priority at Urgent Review (min 85)
        if has_burst:
            total_score = max(total_score, 85.0)

        # Categorization
        if quality_report and quality_report.data_quality_score < 40.0:
            category = "INSUFFICIENT_DATA"
            badge = config.PRIORITY_TIERS["INSUFFICIENT_DATA"]
        elif total_score >= 80.0:
            category = "URGENT_REVIEW"
            badge = config.PRIORITY_TIERS["URGENT_REVIEW"]
        elif total_score >= 60.0:
            category = "INSPECTION_RECOMMENDED"
            badge = config.PRIORITY_TIERS["INSPECTION_RECOMMENDED"]
        elif total_score >= 30.0:
            category = "MONITOR"
            badge = config.PRIORITY_TIERS["MONITOR"]
        else:
            category = "NORMAL"
            badge = config.PRIORITY_TIERS["NORMAL"]

        # Estimated condition grade (clearly noted as assessment, not physical inspection)
        if total_score >= 80.0:
            cond_grade = "Grade 5 - Critical (Severe defect/failure risk, immediate intervention)"
        elif total_score >= 60.0:
            cond_grade = "Grade 4 - Poor (Significant deterioration, physical inspection needed)"
        elif total_score >= 45.0:
            cond_grade = "Grade 3 - Moderate (Signs of deterioration, plan maintenance)"
        elif total_score >= 25.0:
            cond_grade = "Grade 2 - Good (Expected aging, minor service)"
        else:
            cond_grade = "Grade 1 - Very Good (Minor cosmetic wear)"

        # Actionable recommendation
        recommendation = RecommendationGenerator.generate_recommendation(
            segment=segment,
            priority_category=category,
            immediate_anomaly_score=immediate_score,
            long_term_deterioration_score=long_term_score,
            contributing_reasons=reasons,
            has_burst=has_burst,
            has_leak=has_leak,
            has_surge=has_surge,
            has_sensor_fault=has_sensor_fault,
        )

        return RiskAssessmentResult(
            segment_id=seg_id,
            priority_score=total_score,
            priority_category=category,
            badge_label=badge["badge"],
            badge_color=badge["color"],
            immediate_anomaly_score=immediate_score,
            long_term_asset_score=long_term_score,
            estimated_condition_grade=cond_grade,
            factor_breakdown=breakdown,
            contributing_reasons=reasons,
            recommended_response=recommendation,
            data_quality_valid=(quality_report.is_valid_for_analysis if quality_report else True),
        )
