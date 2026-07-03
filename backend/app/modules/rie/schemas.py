"""Pydantic schemas for RIE — risk index and MIDE."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RiskWeights(BaseModel):
    """AHP weights for risk score. RIE-01"""

    metabolic_cost: float = Field(ge=0)
    velocity_degradation: float = Field(ge=0)
    climate_stress: float = Field(ge=0)
    terrain_friction: float = Field(ge=0)


class ClimateFactors(BaseModel):
    """Climate/risk factors applied to a segment. CLI-08, RIE-03 to RIE-06"""

    wbgt: float
    precip_mm: float
    uv_index: float
    cardiovascular_multiplier: float
    climate_cost_multiplier: float
    fc_precipitation: float
    fc_erodability: float
    fc_anegamiento: float
    fc_brillo_solar: float


class MideDimensions(BaseModel):
    """MIDE dimensions from 1 to 5. RIE-08"""

    severity: int = Field(ge=1, le=5)
    orientation: int = Field(ge=1, le=5)
    displacement: int = Field(ge=1, le=5)
    effort: int = Field(ge=1, le=5)


class SegmentRiskOut(BaseModel):
    """Per-segment risk output."""

    risk_score: int = Field(ge=0, le=100)
    is_top_risk: bool
    mide_dimensions: MideDimensions
    climate_factors: ClimateFactors


class RouteRiskSummary(BaseModel):
    """Route-level risk output."""

    mide_global: int = Field(ge=1, le=5)
    mide_dimensions: MideDimensions
    ccr: float
