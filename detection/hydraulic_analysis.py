"""
Hydraulic Analysis and Pressure Gradient Engine
Analyzes pressure deviations, hydraulic gradient, frictional head loss, and pressure transients (surge/hammer).
"""
from dataclasses import dataclass
from typing import Dict, Any, Optional
import math
import config


@dataclass
class HydraulicAnomaly:
    segment_id: str
    measured_pressure_bar: float
    nominal_pressure_bar: float
    pressure_delta_bar: float
    expected_friction_loss_bar: float
    is_anomaly: bool
    anomaly_type: str  # NORMAL, SUDDEN_BURST_DROP, GRADUAL_SLUMP, TRANSIENT_SURGE, LOW_PRESSURE
    severity: str      # NONE, LOW, MEDIUM, HIGH, CRITICAL
    explanation: str


class HydraulicAnalyzer:
    """Evaluates pipe segment pressure telemetry against hydraulic friction models and operational thresholds."""

    @staticmethod
    def estimate_hazen_williams_loss_bar(
        length_km: float,
        diameter_mm: int,
        flow_m3h: float,
        material: str,
    ) -> float:
        """Estimates expected frictional head loss using empirical Hazen-Williams formula:
        h_f (m) = 10.67 * L / (C^1.852 * D^4.87) * Q^1.852
        Returns pressure drop in bar (1 bar ~ 10.197 m head).
        """
        if flow_m3h <= 0 or diameter_mm <= 0 or length_km <= 0:
            return 0.0

        # Hazen-Williams roughness coefficient C
        c_factors = {
            "HDPE": 145.0,
            "Ductile Iron": 130.0,
            "Steel": 120.0,
            "Prestressed Concrete": 115.0,
            "Cast Iron": 100.0,
            "Asbestos-Cement": 110.0,
        }
        c = c_factors.get(material, 120.0)

        # Convert units: L in meters, D in meters, Q in m³/s
        l_m = length_km * 1000.0
        d_m = diameter_mm / 1000.0
        q_m3s = flow_m3h / 3600.0

        head_loss_m = 10.67 * (l_m / (c ** 1.852 * d_m ** 4.8704)) * (q_m3s ** 1.852)
        # Convert head loss in meters to bar: P (bar) = rho * g * h / 100000 ~ h / 10.197
        loss_bar = head_loss_m / 10.197
        return round(loss_bar, 3)

    @classmethod
    def analyze_pressure(
        cls,
        segment: Dict[str, Any],
        measured_pressure_bar: Optional[float],
        measured_flow_m3h: Optional[float] = None,
    ) -> HydraulicAnomaly:
        seg_id = segment["segment_id"]
        nominal = segment["nominal_pressure_bar"]

        if measured_pressure_bar is None:
            return HydraulicAnomaly(
                segment_id=seg_id,
                measured_pressure_bar=0.0,
                nominal_pressure_bar=nominal,
                pressure_delta_bar=0.0,
                expected_friction_loss_bar=0.0,
                is_anomaly=True,
                anomaly_type="INSUFFICIENT_DATA",
                severity="MEDIUM",
                explanation=f"Telemetry unavailable for segment {seg_id}. Cannot compute hydraulic gradient.",
            )

        delta = measured_pressure_bar - nominal
        flow = measured_flow_m3h or segment["nominal_flow_m3h"]
        expected_friction_bar = cls.estimate_hazen_williams_loss_bar(
            segment["length_km"],
            segment["diameter_mm"],
            flow,
            segment["material"]
        )

        # 1. Sudden massive collapse (Burst)
        if delta < -config.THRESHOLDS["pressure_burst_drop_bar"]:
            return HydraulicAnomaly(
                segment_id=seg_id,
                measured_pressure_bar=measured_pressure_bar,
                nominal_pressure_bar=nominal,
                pressure_delta_bar=delta,
                expected_friction_loss_bar=expected_friction_bar,
                is_anomaly=True,
                anomaly_type="SUDDEN_BURST_DROP",
                severity="CRITICAL",
                explanation=(
                    f"Severe pressure collapse of {abs(delta):.2f} bar below nominal ({measured_pressure_bar:.2f} vs {nominal:.2f} bar). "
                    f"Exceeds frictional loss ({expected_friction_bar:.2f} bar); suggests pipe rupture or open hydrant."
                ),
            )

        # 2. Gradual depression (Slump / Developing Leak)
        if delta < -0.40:
            return HydraulicAnomaly(
                segment_id=seg_id,
                measured_pressure_bar=measured_pressure_bar,
                nominal_pressure_bar=nominal,
                pressure_delta_bar=delta,
                expected_friction_loss_bar=expected_friction_bar,
                is_anomaly=True,
                anomaly_type="GRADUAL_SLUMP",
                severity="HIGH",
                explanation=(
                    f"Noticeable pressure depression of {abs(delta):.2f} bar below nominal ({measured_pressure_bar:.2f} vs {nominal:.2f} bar). "
                    f"Indicates localized loss of head or persistent outflow."
                ),
            )

        # 3. Transient surge / Water Hammer
        if delta > config.THRESHOLDS["pressure_surge_spike_bar"]:
            return HydraulicAnomaly(
                segment_id=seg_id,
                measured_pressure_bar=measured_pressure_bar,
                nominal_pressure_bar=nominal,
                pressure_delta_bar=delta,
                expected_friction_loss_bar=expected_friction_bar,
                is_anomaly=True,
                anomaly_type="TRANSIENT_SURGE",
                severity="HIGH",
                explanation=(
                    f"Excessive pressure spike (+{delta:.2f} bar above nominal: {measured_pressure_bar:.2f} bar). "
                    f"Consistent with water hammer, rapid valve closure, or pump check-valve slam."
                ),
            )

        # 4. Low pressure warning (operating near minimum distribution threshold)
        if measured_pressure_bar < config.THRESHOLDS["pressure_min_normal"]:
            return HydraulicAnomaly(
                segment_id=seg_id,
                measured_pressure_bar=measured_pressure_bar,
                nominal_pressure_bar=nominal,
                pressure_delta_bar=delta,
                expected_friction_loss_bar=expected_friction_bar,
                is_anomaly=True,
                anomaly_type="LOW_PRESSURE",
                severity="MEDIUM",
                explanation=(
                    f"Pressure has fallen to {measured_pressure_bar:.2f} bar, below service minimum standard "
                    f"({config.THRESHOLDS['pressure_min_normal']} bar). Customer delivery pressure compromised."
                ),
            )

        # Normal condition
        return HydraulicAnomaly(
            segment_id=seg_id,
            measured_pressure_bar=measured_pressure_bar,
            nominal_pressure_bar=nominal,
            pressure_delta_bar=delta,
            expected_friction_loss_bar=expected_friction_bar,
            is_anomaly=False,
            anomaly_type="NORMAL",
            severity="NONE",
            explanation=f"Hydraulic pressure ({measured_pressure_bar:.2f} bar) is within normal operating envelope.",
        )
