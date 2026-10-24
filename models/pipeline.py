"""
Pipeline, Network, Station, and Storage Asset Data Models
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class WaterSource:
    source_id: str
    name: str
    source_type: str  # Dam, River Intake, Wellfield
    capacity_m3: float
    current_storage_pct: float
    safe_yield_m3h: float
    status: str = "Operating"


@dataclass
class TreatmentPlant:
    plant_id: str
    name: str
    source_id: str
    design_capacity_m3h: float
    current_throughput_m3h: float
    chlorine_residual_ppm: float = 1.2
    turbidity_ntu: float = 0.4
    status: str = "Operating"


@dataclass
class MonitoringStation:
    station_id: str
    name: str
    segment_id: str
    stage: str
    elevation_m: float
    has_pressure_sensor: bool = True
    has_flow_meter: bool = True
    has_acoustic_sensor: bool = True
    has_reservoir_sensor: bool = False
    is_active: bool = True


@dataclass
class Reservoir:
    reservoir_id: str
    name: str
    connected_segment_id: str
    capacity_m3: float
    current_level_m: float
    max_level_m: float
    current_storage_pct: float
    low_level_threshold_pct: float = 25.0
    status: str = "Normal"


@dataclass
class PipelineSegment:
    segment_id: str
    name: str
    stage: str  # Transmission, Distribution, Intake
    upstream_station_id: str
    downstream_station_id: str
    length_km: float
    diameter_mm: int
    material: str  # Ductile Iron, Cast Iron, HDPE, Steel, Asbestos-Cement
    installation_year: int
    nominal_pressure_bar: float
    nominal_flow_m3h: float
    criticality: str  # Critical, High, Medium, Low
    soil_condition: str = "Moderate"  # Non-corrosive, Moderate, Corrosive, Clay
    burial_depth_m: float = 1.5
    past_repair_count: int = 0
    last_inspection_date: Optional[str] = None
    nearby_excavation_risk: bool = False
    connected_reservoir_id: Optional[str] = None

    @property
    def age_years(self) -> int:
        from datetime import datetime
        current_year = datetime.now().year
        return max(0, current_year - self.installation_year)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "segment_id": self.segment_id,
            "name": self.name,
            "stage": self.stage,
            "upstream_station_id": self.upstream_station_id,
            "downstream_station_id": self.downstream_station_id,
            "length_km": self.length_km,
            "diameter_mm": self.diameter_mm,
            "material": self.material,
            "installation_year": self.installation_year,
            "age_years": self.age_years,
            "nominal_pressure_bar": self.nominal_pressure_bar,
            "nominal_flow_m3h": self.nominal_flow_m3h,
            "criticality": self.criticality,
            "soil_condition": self.soil_condition,
            "past_repair_count": self.past_repair_count,
            "last_inspection_date": self.last_inspection_date,
            "nearby_excavation_risk": self.nearby_excavation_risk,
            "connected_reservoir_id": self.connected_reservoir_id,
        }
