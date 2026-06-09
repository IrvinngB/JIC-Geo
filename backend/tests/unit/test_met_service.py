"""Unit tests for MET module — validates against reference values from Formulas.md."""

import pytest

from app.modules.met.service import minetti_cot, pandolf_metabolic_rate


class TestMinettiCoT:
    """Reference values from Formulas.md Table 2.1."""

    def test_flat_terrain(self):
        cot, method = minetti_cot(0.0)
        assert abs(cot - 2.5) < 0.1
        assert method == "exact"

    def test_optimal_descent(self):
        """Optimal descent (~-10%) should be the absolute minimum CoT (~0.81)."""
        cot, method = minetti_cot(-0.10)
        assert abs(cot - 0.81) < 0.15
        assert method == "exact"

    def test_extreme_ascent_extrapolated(self):
        """Gradient 0.60 is outside Minetti domain — should extrapolate, never negative."""
        cot, method = minetti_cot(0.60)
        assert method == "extrapolated"
        assert cot >= 0.0

    def test_extreme_descent_extrapolated(self):
        cot, method = minetti_cot(-0.60)
        assert method == "extrapolated"
        assert cot >= 0.0

    def test_domain_boundaries_are_exact(self):
        _, method_min = minetti_cot(-0.45)
        _, method_max = minetti_cot(0.45)
        assert method_min == "exact"
        assert method_max == "exact"


class TestPandolfMetabolicRate:
    def test_returns_positive_value(self):
        rate = pandolf_metabolic_rate(
            weight_kg=70,
            load_kg=10,
            velocity_ms=1.4,  # ~5 km/h
            slope_pct=0.0,
            terrain_eta=1.2,
        )
        assert rate > 0
