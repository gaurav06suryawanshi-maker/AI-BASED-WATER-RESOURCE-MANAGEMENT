"""
Explainable Recommendation Engine
Produces plain-language, actionable engineering maintenance advice.
Separates immediate sensor anomaly mitigation from long-term asset rehabilitation.
"""
from typing import List, Dict, Any, Optional
import config


class RecommendationGenerator:
    """Translates multi-dimensional risk scores and telemetry evidence into prioritized engineering responses."""

    @staticmethod
    def generate_recommendation(
        segment: Dict[str, Any],
        priority_category: str,
        immediate_anomaly_score: float,
        long_term_deterioration_score: float,
        contributing_reasons: List[str],
        has_burst: bool = False,
        has_leak: bool = False,
        has_surge: bool = False,
        has_sensor_fault: bool = False,
    ) -> str:
        seg_id = segment["segment_id"]
        seg_name = segment["name"]
        material = segment["material"]
        age = segment.get("age_years", 0)

        # 1. Catastrophic burst condition
        if has_burst:
            return (
                f"CRITICAL ACTION: Immediate physical isolation recommended for {seg_id} ({seg_name}). "
                "Close upstream isolation valves to halt mass water discharge. Dispatch emergency excavation crew, "
                "notify municipal traffic management for road closure, and reroute distribution supply via backup loops."
            )

        # 2. Suspected active leakage
        if has_leak:
            return (
                f"HIGH PRIORITY: Repeated pressure depression and a persistent flow imbalance were corroborated by elevated "
                f"acoustic indices on {seg_id}. Verify telemetry calibration, then deploy a leak detection crew with acoustic "
                f"ground microphones and correlators along the {segment['length_km']:.1f} km section within 24 hours."
            )

        # 3. Transient surge / water hammer
        if has_surge:
            return (
                f"HYDRAULIC REVIEW: Sudden pressure surge detected on {seg_id}. Inspect upstream pump check valves, "
                "verify operational readiness of air-relief valves, and inspect surge anticipator damping chambers to prevent cyclical pipe fatigue."
            )

        # 4. Sensor telemetry fault
        if has_sensor_fault:
            return (
                f"INSTRUMENTATION CHECK: Transducer or gateway communication fault flagged on {seg_id}. "
                "Verify sensor calibration and power supply before conducting physical excavation or relying on automated leak diagnostics."
            )

        # 5. Long-term deterioration with high inspection score
        if priority_category == "URGENT_REVIEW":
            return (
                f"URGENT REVIEW: Segment {seg_id} ({material}, {age} years old) exhibits high cumulative vulnerability "
                f"({segment['past_repair_count']} past repairs, corrosive soil). Arrange non-destructive condition assessment "
                "(electromagnetic thickness scanning or closed-circuit CCTV) within 14 days."
            )

        if priority_category == "INSPECTION_RECOMMENDED":
            return (
                f"INSPECTION RECOMMENDED: Elevated risk profile observed for {seg_id} due to asset aging ({age} years) "
                f"and strategic criticality ({segment['criticality']}). Schedule preventative visual chamber inspection "
                "and valve exercise within the next monthly maintenance cycle."
            )

        if priority_category == "MONITOR":
            return (
                f"CONTINUED MONITORING: Operating within acceptable hydraulic tolerances, but asset profile merits tracking. "
                "Review minimum night flow trends weekly and ensure cathodic protection is active."
            )

        # Normal condition
        return (
            f"ROUTINE MAINTENANCE: {seg_id} operating nominally with healthy sensors. "
            "Maintain standard preventative inspection interval (annual cycle)."
        )
