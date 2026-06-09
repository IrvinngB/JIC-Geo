"""Unit tests for VEL module — validates Tobler and Irmischer-Clarke models."""

from app.modules.vel.service import VelocityModel, calculate_velocity, tobler


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


class TestVelocityDispatch:
    def test_tobler_model_selected(self):
        v = calculate_velocity(slope=0.0, model=VelocityModel.TOBLER)
        assert v > 0

    def test_irmischer_model_selected(self):
        v = calculate_velocity(slope=0.0, model=VelocityModel.IRMISCHER_CLARKE)
        assert v > 0
