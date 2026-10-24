"""
Water-Balance and Mass-Conservation Analysis
Implements mass-balance accounting across pipeline segments, monitoring stations, and storage reservoirs:
Discrepancy = Inflow - Outflow - Storage Change - Authorized Withdrawals
Includes measurement uncertainty error propagation (±2% tolerance) to prevent declaring normal meter noise as leakage.
"""
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
import math
import config


@dataclass
class WaterBalanceResult:
    segment_id: str
    inflow_m3h: float
    outflow_m3h: float
    storage_change_m3h: float
    authorized_withdrawal_m3h: float
    unexplained_discrepancy_m3h: float
    discrepancy_pct: float
    uncertainty_band_m3h: float
    is_statistically_significant: bool
    status_label: str
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "segment_id": self.segment_id,
            "inflow_m3h": round(self.inflow_m3h, 2),
            "outflow_m3h": round(self.outflow_m3h, 2),
            "storage_change_m3h": round(self.storage_change_m3h, 2),
            "authorized_withdrawal_m3h": round(self.authorized_withdrawal_m3h, 2),
            "unexplained_discrepancy_m3h": round(self.unexplained_discrepancy_m3h, 2),
            "discrepancy_pct": round(self.discrepancy_pct, 2),
            "uncertainty_band_m3h": round(self.uncertainty_band_m3h, 2),
            "is_statistically_significant": self.is_statistically_significant,
            "status_label": self.status_label,
            "explanation": self.explanation,
        }


class WaterBalanceCalculator:
    """Calculates mass-balance conservation with rigorous error propagation and uncertainty bands."""

    @staticmethod
    def calculate_balance(
        segment_id: str,
        inflow_m3h: float,
        outflow_m3h: float,
        storage_change_m3h: float = 0.0,
        authorized_withdrawal_m3h: float = 0.0,
        meter_uncertainty_pct: float = config.THRESHOLDS["meter_uncertainty_pct"],
    ) -> WaterBalanceResult:
        """Computes mass balance:
        Unexplained Discrepancy = Q_in - Q_out - Delta_S - Q_auth
        Propagates Gaussian root-sum-square sensor uncertainty.
        """
        if inflow_m3h <= 0.0:
            return WaterBalanceResult(
                segment_id=segment_id,
                inflow_m3h=0.0,
                outflow_m3h=outflow_m3h,
                storage_change_m3h=storage_change_m3h,
                authorized_withdrawal_m3h=authorized_withdrawal_m3h,
                unexplained_discrepancy_m3h=0.0,
                discrepancy_pct=0.0,
                uncertainty_band_m3h=0.0,
                is_statistically_significant=False,
                status_label="Zero Inflow / Standby",
                explanation="No flow detected across inlet meter. Pipeline is isolated or offline.",
            )

        # Unexplained difference calculation
        raw_discrepancy = inflow_m3h - outflow_m3h - storage_change_m3h - authorized_withdrawal_m3h
        discrepancy_pct = (raw_discrepancy / inflow_m3h) * 100.0

        # Measurement uncertainty error propagation (95% CI ~ 1.96 * sigma)
        sigma_in = (meter_uncertainty_pct / 100.0) * inflow_m3h
        sigma_out = (meter_uncertainty_pct / 100.0) * max(0.0, outflow_m3h)
        sigma_storage = 0.02 * abs(storage_change_m3h) if storage_change_m3h != 0.0 else 0.0
        sigma_total = math.sqrt(sigma_in ** 2 + sigma_out ** 2 + sigma_storage ** 2)
        uncertainty_band_m3h = 1.96 * sigma_total

        # Statistical significance check
        is_significant = (raw_discrepancy > uncertainty_band_m3h) and (
            discrepancy_pct > config.THRESHOLDS["flow_imbalance_warning_pct"]
            or raw_discrepancy > config.THRESHOLDS["min_flow_discrepancy_m3h"]
        )

        # Labeling according to prompt guidelines (honestly as unexplained difference)
        if raw_discrepancy <= uncertainty_band_m3h:
            status_label = "Balanced (Within Meter Tolerance)"
            explanation = (
                f"Discrepancy ({raw_discrepancy:.1f} m³/h, {discrepancy_pct:.1f}%) is within the ±{uncertainty_band_m3h:.1f} m³/h "
                f"composite meter uncertainty band (±{meter_uncertainty_pct}% calibration rating). No unexplained loss detected."
            )
        elif discrepancy_pct > config.THRESHOLDS["flow_imbalance_critical_pct"]:
            status_label = "Severe Unexplained Flow Deficit"
            explanation = (
                f"Severe flow discrepancy of {raw_discrepancy:.1f} m³/h ({discrepancy_pct:.1f}%) significantly exceeds "
                f"uncertainty band (±{uncertainty_band_m3h:.1f} m³/h). Indicates potential pipeline breach or major unmetered withdrawal."
            )
        else:
            status_label = "Moderate Unexplained Discrepancy"
            explanation = (
                f"Unexplained flow difference of {raw_discrepancy:.1f} m³/h ({discrepancy_pct:.1f}%) exceeds standard "
                f"meter tolerance (±{uncertainty_band_m3h:.1f} m³/h). Secondary confirmation (pressure/acoustics) required."
            )

        return WaterBalanceResult(
            segment_id=segment_id,
            inflow_m3h=inflow_m3h,
            outflow_m3h=outflow_m3h,
            storage_change_m3h=storage_change_m3h,
            authorized_withdrawal_m3h=authorized_withdrawal_m3h,
            unexplained_discrepancy_m3h=raw_discrepancy,
            discrepancy_pct=discrepancy_pct,
            uncertainty_band_m3h=uncertainty_band_m3h,
            is_statistically_significant=is_significant,
            status_label=status_label,
            explanation=explanation,
        )

    @classmethod
    def calculate_system_summary(cls, balance_results: List[WaterBalanceResult]) -> Dict[str, Any]:
        """Aggregates all segment balances to compute system-wide volumetric conservation."""
        total_inflow = sum(r.inflow_m3h for r in balance_results)
        total_outflow = sum(r.outflow_m3h for r in balance_results)
        total_storage_delta = sum(r.storage_change_m3h for r in balance_results)
        total_auth = sum(r.authorized_withdrawal_m3h for r in balance_results)
        total_discrepancy = sum(r.unexplained_discrepancy_m3h for r in balance_results if r.unexplained_discrepancy_m3h > 0)
        overall_pct = (total_discrepancy / total_inflow * 100.0) if total_inflow > 0 else 0.0

        return {
            "total_inflow_m3h": round(total_inflow, 2),
            "total_outflow_m3h": round(total_outflow, 2),
            "total_storage_delta_m3h": round(total_storage_delta, 2),
            "total_authorized_m3h": round(total_auth, 2),
            "total_unexplained_discrepancy_m3h": round(total_discrepancy, 2),
            "overall_discrepancy_pct": round(overall_pct, 2),
            "segments_with_discrepancy": [r.segment_id for r in balance_results if r.is_statistically_significant],
        }
