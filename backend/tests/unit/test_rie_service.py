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


# ---------------------------------------------------------------------------
# IDR 5-level reachability tests — Tabla 3 del artículo
# ---------------------------------------------------------------------------

_DEFAULT_WEIGHTS = RiskWeights(
    metabolic_cost=0.35,
    velocity_degradation=0.25,
    climate_stress=0.25,
    terrain_friction=0.15,
)


def test_mild_conditions_stay_in_level_1() -> None:
    """Flat trail, no heat, no rain → IDR < 20 (green)."""
    score, _ = calculate_segment_risk(
        _segment(slope_pct=0.02, wbgt=22.0, cot_j_per_kg_m=2.0, metabolic_rate_w=150.0),
        _DEFAULT_WEIGHTS,
    )
    assert score < 20, f"Expected level 1 (< 20), got {score}"


def test_moderate_slope_reaches_level_2() -> None:
    """Moderate slope + light effort → IDR in [20, 40) (yellow)."""
    score, _ = calculate_segment_risk(
        _segment(slope_pct=0.15, cot_j_per_kg_m=6.0, metabolic_rate_w=350.0),
        _DEFAULT_WEIGHTS,
    )
    assert 20 <= score < 40, f"Expected level 2 [20, 40), got {score}"


def test_steep_slope_with_heat_reaches_level_3() -> None:
    """Steep slope + moderate heat stress → IDR in [40, 60) (orange)."""
    score, _ = calculate_segment_risk(
        _segment(
            slope_pct=0.30,
            cot_j_per_kg_m=10.0,
            metabolic_rate_w=500.0,
            wbgt=30.0,
            elapsed_time_min=60.0,
            canopy_density=0.2,
            velocity_kmh=3.0,
        ),
        _DEFAULT_WEIGHTS,
    )
    assert 40 <= score < 60, f"Expected level 3 [40, 60), got {score}"


def test_extreme_terrain_with_heat_reaches_level_4() -> None:
    """Very steep + high WBGT + velocity degradation → IDR in [60, 80) (red)."""
    score, _ = calculate_segment_risk(
        _segment(
            slope_pct=0.40,
            cot_j_per_kg_m=14.0,
            metabolic_rate_w=600.0,
            wbgt=32.0,
            elapsed_time_min=120.0,
            canopy_density=0.1,
            velocity_kmh=2.0,
            uv_index=10.0,
        ),
        _DEFAULT_WEIGHTS,
    )
    assert 60 <= score < 80, f"Expected level 4 [60, 80), got {score}"


def test_all_components_maxed_reaches_level_5() -> None:
    """Everything at worst case → IDR >= 80 (purple)."""
    score, _ = calculate_segment_risk(
        _segment(
            slope_pct=0.50,
            cot_j_per_kg_m=20.0,
            metabolic_rate_w=800.0,
            wbgt=36.0,
            elapsed_time_min=180.0,
            canopy_density=0.0,
            surface_type="mud",
            is_on_path=False,
            velocity_kmh=0.5,
            precip_mm=30.0,
            uv_index=12.0,
        ),
        _DEFAULT_WEIGHTS,
    )
    assert score >= 80, f"Expected level 5 (>= 80), got {score}"


def test_theoretical_max_approaches_100() -> None:
    """With every component clamped at 1.0 the score should reach ~100."""
    score, _ = calculate_segment_risk(
        _segment(
            slope_pct=0.60,
            cot_j_per_kg_m=25.0,
            metabolic_rate_w=1000.0,
            wbgt=40.0,
            elapsed_time_min=300.0,
            canopy_density=0.0,
            surface_type="mud",
            is_on_path=False,
            velocity_kmh=0.1,
            precip_mm=50.0,
            uv_index=14.0,
        ),
        _DEFAULT_WEIGHTS,
    )
    assert score >= 95, f"Expected near-max (>= 95), got {score}"


def test_each_component_contributes_independently() -> None:
    """Verify that increasing each risk dimension actually raises the score."""
    baseline, _ = calculate_segment_risk(_segment(), _DEFAULT_WEIGHTS)

    # High metabolic only
    high_met, _ = calculate_segment_risk(
        _segment(cot_j_per_kg_m=18.0, metabolic_rate_w=750.0), _DEFAULT_WEIGHTS
    )
    assert high_met > baseline, "Metabolic component should raise score"

    # High velocity degradation only
    high_vel, _ = calculate_segment_risk(
        _segment(velocity_kmh=1.0), _DEFAULT_WEIGHTS
    )
    assert high_vel > baseline, "Velocity degradation should raise score"

    # High climate only
    high_cli, _ = calculate_segment_risk(
        _segment(wbgt=35.0, elapsed_time_min=120.0, canopy_density=0.0), _DEFAULT_WEIGHTS
    )
    assert high_cli > baseline, "Climate stress should raise score"

    # High terrain only
    high_ter, _ = calculate_segment_risk(
        _segment(slope_pct=0.45, is_on_path=False), _DEFAULT_WEIGHTS
    )
    assert high_ter > baseline, "Terrain friction should raise score"
