"""Unit tests for VEL module — validates Tobler, Irmischer-Clarke, and Langmuir."""

import math

import pytest

from app.modules.vel.service import (
    VelocityModel,
    apply_langmuir,
    calculate_velocity,
    tobler,
    irmischer_clarke,
)


class TestTobler:
    def test_flat_terrain_is_5kmh(self):
        v = tobler(slope=0.0)
        assert abs(v - 5.0) < 0.1

    def test_optimal_slope_is_6kmh(self):
        """Maximum velocity at S ≈ -0.05 (−2.86°)."""
        v = tobler(slope=-0.05)
        assert abs(v - 6.0) < 0.05

    def test_off_path_factor(self):
        """Off-path velocity must be 60% of on-path."""
        on = tobler(slope=0.0, is_on_path=True)
        off = tobler(slope=0.0, is_on_path=False)
        assert abs(off - on * 0.6) < 0.01

    def test_steep_ascent_reduces_velocity(self):
        v_flat = tobler(0.0)
        v_steep = tobler(0.5)
        assert v_steep < v_flat


class TestIrmischerClarke:
    def test_flat_terrain_is_approx_3_9_kmh(self):
        v = irmischer_clarke(slope=0.0)
        assert abs(v - 3.89) < 0.05

    def test_optimal_slope_is_4kmh(self):
        """Maximum velocity at S ≈ -0.0506."""
        v = irmischer_clarke(slope=-0.0506)
        assert abs(v - 4.0) < 0.01

    def test_off_path_factor(self):
        """Off-path velocity must be 60% of on-path."""
        on = irmischer_clarke(slope=0.0, is_on_path=True)
        off = irmischer_clarke(slope=0.0, is_on_path=False)
        assert abs(off - on * 0.6) < 0.01

    def test_steep_ascent_reduces_velocity(self):
        v_flat = irmischer_clarke(0.0)
        v_steep = irmischer_clarke(0.5)
        assert v_steep < v_flat


class TestLangmuir:
    def test_gentle_descent_increases_speed(self):
        """5°–12° descent: -10 min / 300 m → speed should increase."""
        v_base = 1.0  # slow enough that -10 min still leaves positive time
        v_adj = apply_langmuir(v_base, slope_deg=8.0, is_descent=True)
        assert v_adj > v_base

    def test_steep_descent_decreases_speed(self):
        """ >12° descent: +10 min / 300 m → speed should decrease."""
        v_base = 5.0
        v_adj = apply_langmuir(v_base, slope_deg=15.0, is_descent=True)
        assert v_adj < v_base

    def test_no_effect_on_ascent(self):
        v_base = 5.0
        v_adj = apply_langmuir(v_base, slope_deg=8.0, is_descent=False)
        assert v_adj == v_base

    def test_no_effect_on_flat(self):
        v_base = 5.0
        v_adj = apply_langmuir(v_base, slope_deg=0.0, is_descent=True)
        assert v_adj == v_base


class TestVelocityDispatch:
    def test_tobler_model_selected(self):
        v = calculate_velocity(slope=0.0, model=VelocityModel.TOBLER)
        assert v > 0

    def test_irmischer_model_selected(self):
        v = calculate_velocity(slope=0.0, model=VelocityModel.IRMISCHER_CLARKE)
        assert v > 0

    def test_langmuir_applied_on_descent(self):
        v = calculate_velocity(slope=-0.10, model=VelocityModel.TOBLER, apply_langmuir_correction=True)
        assert v > 0
