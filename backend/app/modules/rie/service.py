"""RIE service — pure risk, Cifuentes, and MIDE calculations."""

from __future__ import annotations

import math
from dataclasses import dataclass

from app.modules.cli.service import climate_cost_multiplier, cardiovascular_drift_multiplier
from app.modules.rie.schemas import ClimateFactors, MideDimensions, RiskWeights, RouteRiskSummary


@dataclass(frozen=True)
class SegmentRiskInput:
    seq: int
    slope_pct: float
    velocity_kmh: float
    baseline_velocity_kmh: float
    cot_j_per_kg_m: float
    metabolic_rate_w: float
    elapsed_time_min: float
    segment_time_min: float
    canopy_density: float
    surface_type: str
    is_on_path: bool
    wbgt: float
    precip_mm: float
    uv_index: float


def normalize_weights(weights: RiskWeights) -> RiskWeights:
    """Normalize AHP weights so small config mistakes do not skew scores. RIE-01"""
    total = (
        weights.metabolic_cost
        + weights.velocity_degradation
        + weights.climate_stress
        + weights.terrain_friction
    )
    if total <= 0:
        return RiskWeights(
            metabolic_cost=0.35,
            velocity_degradation=0.25,
            climate_stress=0.25,
            terrain_friction=0.15,
        )
    return RiskWeights(
        metabolic_cost=weights.metabolic_cost / total,
        velocity_degradation=weights.velocity_degradation / total,
        climate_stress=weights.climate_stress / total,
        terrain_friction=weights.terrain_friction / total,
    )


def cifuentes_factor(limiting_magnitude: float, total_magnitude: float) -> float:
    """Return Fc_i = 1 - (ml_i / mt). RIE-02"""
    if total_magnitude <= 0:
        return 1.0
    return round(max(0.0, min(1.0, 1.0 - (limiting_magnitude / total_magnitude))), 4)


def cifuentes_correction_factors(
    precip_mm: float,
    slope_pct: float,
    canopy_density: float,
    surface_type: str,
    uv_index: float,
) -> dict[str, float]:
    """Return Cifuentes correction factors. RIE-03 to RIE-06"""
    precipitation_limiting = min(1.0, precip_mm / 40.0)
    erodability_limiting = 0.0
    if surface_type in {"mud", "sand", "scrub"} and abs(slope_pct) > 0.10:
        erodability_limiting = min(1.0, abs(slope_pct) * (1.5 if abs(slope_pct) > 0.20 else 1.0))
    anegamiento_limiting = 0.7 if surface_type == "mud" and precip_mm > 10.0 else 0.0
    solar_limiting = (1.0 - canopy_density) if uv_index >= 8.0 else 0.0
    return {
        "fc_precipitation": cifuentes_factor(precipitation_limiting, 1.0),
        "fc_erodability": cifuentes_factor(erodability_limiting, 1.0),
        "fc_anegamiento": cifuentes_factor(anegamiento_limiting, 1.0),
        "fc_brillo_solar": cifuentes_factor(solar_limiting, 1.0),
    }


def calculate_ccf(length_m: float, space_per_group_m: float = 2.0, visit_hours: float = 8.0, route_time_h: float = 1.0) -> float:
    """Return physical carrying capacity CCF. RIE-07"""
    visits_per_day = visit_hours / max(route_time_h, 0.1)
    return (length_m / max(space_per_group_m, 0.1)) * visits_per_day


def calculate_ccr(ccf: float, factors: list[float]) -> float:
    """Return real carrying capacity CCR = CCF * product(Fc_i). RIE-07"""
    product = 1.0
    for factor in factors:
        product *= max(0.0, min(1.0, factor))
    return round(ccf * product, 2)


def calculate_segment_risk(
    segment: SegmentRiskInput,
    weights: RiskWeights,
) -> tuple[int, ClimateFactors]:
    """Calculate risk score from metabolic, velocity, climate, and terrain factors. RIE-01"""
    normalized = normalize_weights(weights)
    cv_multiplier = cardiovascular_drift_multiplier(segment.elapsed_time_min, segment.wbgt)
    cost_multiplier = climate_cost_multiplier(
        wbgt=segment.wbgt,
        precip_mm=segment.precip_mm,
        slope_pct=segment.slope_pct,
        canopy_density=segment.canopy_density,
    )
    factors = cifuentes_correction_factors(
        precip_mm=segment.precip_mm,
        slope_pct=segment.slope_pct,
        canopy_density=segment.canopy_density,
        surface_type=segment.surface_type,
        uv_index=segment.uv_index,
    )
    metabolic_component = min(1.0, max(segment.cot_j_per_kg_m / 18.0, segment.metabolic_rate_w / 750.0))
    velocity_degradation = 1.0 - min(1.0, segment.velocity_kmh / max(segment.baseline_velocity_kmh, 0.1))
    climate_component = min(1.0, ((cv_multiplier - 1.0) / 2.0) + ((cost_multiplier - 1.0) / 2.0))
    terrain_component = min(1.0, abs(segment.slope_pct) / 0.45 + (0.15 if not segment.is_on_path else 0.0))
    score = (
        normalized.metabolic_cost * metabolic_component
        + normalized.velocity_degradation * velocity_degradation
        + normalized.climate_stress * climate_component
        + normalized.terrain_friction * terrain_component
    )
    climate_factors = ClimateFactors(
        wbgt=segment.wbgt,
        precip_mm=segment.precip_mm,
        uv_index=segment.uv_index,
        cardiovascular_multiplier=cv_multiplier,
        climate_cost_multiplier=cost_multiplier,
        **factors,
    )
    return min(100, max(0, round(score * 100))), climate_factors


def mark_top_risk(scores_by_seq: dict[int, int]) -> set[int]:
    """Return the top 10% highest risk segment seqs. RIE-10"""
    if not scores_by_seq:
        return set()
    top_count = max(1, math.ceil(len(scores_by_seq) * 0.1))
    return {
        seq
        for seq, _ in sorted(scores_by_seq.items(), key=lambda item: item[1], reverse=True)[
            :top_count
        ]
    }


def mide_effort_level(total_time_h: float) -> int:
    """Map route time to MIDE effort. RIE-08"""
    if total_time_h < 1:
        return 1
    if total_time_h < 3:
        return 2
    if total_time_h < 5:
        return 3
    if total_time_h < 8:
        return 4
    return 5


def calculate_mide_dimensions(
    max_risk_score: int,
    max_abs_slope: float,
    off_path_ratio: float,
    total_time_h: float,
    wbgt: float,
) -> MideDimensions:
    """Translate algorithmic risk into four MIDE dimensions. RIE-08"""
    severity = 1
    if max_risk_score >= 80 or wbgt >= 32:
        severity = 5
    elif max_risk_score >= 65 or wbgt >= 30:
        severity = 4
    elif max_risk_score >= 45 or wbgt >= 28:
        severity = 3
    elif max_risk_score >= 25:
        severity = 2

    orientation = min(5, max(1, 1 + math.ceil(off_path_ratio * 4)))
    displacement = 1
    if max_abs_slope >= 0.45:
        displacement = 5
    elif max_abs_slope >= 0.30:
        displacement = 4
    elif max_abs_slope >= 0.18:
        displacement = 3
    elif max_abs_slope >= 0.08:
        displacement = 2

    return MideDimensions(
        severity=severity,
        orientation=orientation,
        displacement=displacement,
        effort=mide_effort_level(total_time_h),
    )


def mide_global(dimensions: MideDimensions) -> int:
    """Return weighted global MIDE level. RIE-09"""
    value = (
        dimensions.severity * 0.30
        + dimensions.orientation * 0.20
        + dimensions.displacement * 0.20
        + dimensions.effort * 0.30
    )
    return min(5, max(1, round(value)))


def summarize_route_risk(
    scores_by_seq: dict[int, int],
    max_abs_slope: float,
    off_path_ratio: float,
    total_time_h: float,
    wbgt: float,
    total_length_m: float,
) -> RouteRiskSummary:
    """Return route-level MIDE and CCR summary. RIE-07 to RIE-09"""
    max_risk = max(scores_by_seq.values()) if scores_by_seq else 0
    dimensions = calculate_mide_dimensions(max_risk, max_abs_slope, off_path_ratio, total_time_h, wbgt)
    correction = max(0.1, 1.0 - (max_risk / 100.0) * 0.6)
    ccf = calculate_ccf(total_length_m, route_time_h=total_time_h)
    ccr = calculate_ccr(ccf, [correction])
    return RouteRiskSummary(
        mide_global=mide_global(dimensions),
        mide_dimensions=dimensions,
        ccr=ccr,
    )
