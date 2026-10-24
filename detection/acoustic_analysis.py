"""
Acoustic and Vibration Telemetry Analysis
Detects abnormal pipe sound patterns, high-frequency hiss, cavitation, and turbulent vibration
associated with pressurized pipe orifice discharge.
"""
from dataclasses import dataclass
from typing import Optional
import config


@dataclass
class AcousticAnomaly:
    segment_id: str
    acoustic_index: float
    vibration_rms: float
    is_anomaly: bool
    anomaly_type: str  # NORMAL, ELEVATED_ACOUSTIC_LEAK, HIGH_VIBRATION_BURST, INSUFFICIENT_DATA
    severity: str      # NONE, LOW, MEDIUM, HIGH, CRITICAL
    explanation: str


class AcousticAnalyzer:
    """Evaluates pipe wall acoustic and vibration telemetry to provide physical corroboration for leak detection."""

    @staticmethod
    def analyze(
        segment_id: str,
        acoustic_index: Optional[float],
        vibration_rms: Optional[float],
    ) -> AcousticAnomaly:
        if acoustic_index is None and vibration_rms is None:
            return AcousticAnomaly(
                segment_id=segment_id,
                acoustic_index=0.0,
                vibration_rms=0.0,
                is_anomaly=False,
                anomaly_type="INSUFFICIENT_DATA",
                severity="NONE",
                explanation="Acoustic and vibration telemetry offline or not installed on station.",
            )

        ac_val = acoustic_index if acoustic_index is not None else 15.0
        vib_val = vibration_rms if vibration_rms is not None else 1.0

        # Burst-level vibration and noise
        if ac_val >= config.THRESHOLDS["acoustic_burst_threshold"] or vib_val >= config.THRESHOLDS["vibration_alert"]:
            return AcousticAnomaly(
                segment_id=segment_id,
                acoustic_index=ac_val,
                vibration_rms=vib_val,
                is_anomaly=True,
                anomaly_type="HIGH_VIBRATION_BURST",
                severity="CRITICAL",
                explanation=(
                    f"Extreme acoustic index ({ac_val:.1f}/100) and vibration level ({vib_val:.2f} mm/s RMS). "
                    f"Signature indicates severe structural turbulence or high-velocity jet breach."
                ),
            )

        # Developing leak hiss
        if ac_val >= config.THRESHOLDS["acoustic_leak_threshold"]:
            return AcousticAnomaly(
                segment_id=segment_id,
                acoustic_index=ac_val,
                vibration_rms=vib_val,
                is_anomaly=True,
                anomaly_type="ELEVATED_ACOUSTIC_LEAK",
                severity="HIGH",
                explanation=(
                    f"Elevated acoustic index ({ac_val:.1f}/100) exceeds leak threshold ({config.THRESHOLDS['acoustic_leak_threshold']}). "
                    f"Consistent with continuous pressurized orifice hiss."
                ),
            )

        # Baseline quiet
        return AcousticAnomaly(
            segment_id=segment_id,
            acoustic_index=ac_val,
            vibration_rms=vib_val,
            is_anomaly=False,
            anomaly_type="NORMAL",
            severity="NONE",
            explanation=f"Acoustic baseline ({ac_val:.1f}) and vibration ({vib_val:.2f} mm/s) within normal quiet operating parameters.",
        )
