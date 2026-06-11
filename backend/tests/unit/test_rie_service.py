from app.modules.rie.schemas import RiskWeights
from app.modules.rie.service import (
    SegmentRiskInput,
    calculate_ccr,
    calculate_segment_risk,
    cifuentes_factor,
    mark_top_risk,
    summarize_route_risk,
)


def _segment(**overrides: float | int | str | bool) -> SegmentRiskInput:
    values = {
        "seq": 1,
        "slope_pct": 0.02,
        "velocity_kmh": 5.0,
        "baseline_velocity_kmh": 5.0,
        "cot_j_per_kg_m": 2.5,
        "metabolic_rate_w": 250.0,
        "elapsed_time_min": 10.0,
        "segment_time_min": 5.0,
        "canopy_density": 0.8,
        "surface_type": "dirt",
        "is_on_path": True,
        "wbgt": 24.0,
        "precip_mm": 0.0,
        "uv_index": 3.0,
    }
    values.update(overrides)
    return SegmentRiskInput(**values)


def test_cifuentes_factor_bounds() -> None:
    assert cifuentes_factor(0, 10) == 1.0
    assert cifuentes_factor(5, 10) == 0.5
    assert cifuentes_factor(20, 10) == 0.0


def test_extreme_heat_increases_risk() -> None:
    weights = RiskWeights(
        metabolic_cost=0.35,
        velocity_degradation=0.25,
        climate_stress=0.25,
        terrain_friction=0.15,
    )
    mild_score, _ = calculate_segment_risk(_segment(), weights)
    heat_score, _ = calculate_segment_risk(
        _segment(wbgt=34.0, uv_index=11.0, canopy_density=0.1, elapsed_time_min=80.0),
        weights,
    )

    assert heat_score > mild_score


def test_top_ten_percent_marks_at_least_one() -> None:
    assert mark_top_risk({1: 10, 2: 90, 3: 20}) == {2}


def test_route_mide_dimensions_are_bounded() -> None:
    summary = summarize_route_risk(
        scores_by_seq={1: 90, 2: 50},
        max_abs_slope=0.5,
        off_path_ratio=0.5,
        total_time_h=9.0,
        wbgt=33.0,
        total_length_m=12000,
    )

    assert 1 <= summary.mide_global <= 5
    assert summary.mide_dimensions.severity == 5
    assert summary.mide_dimensions.effort == 5


def test_ccr_multiplies_correction_factors() -> None:
    assert calculate_ccr(100, [0.8, 0.5]) == 40
