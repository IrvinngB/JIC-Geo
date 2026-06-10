"""
Unit tests for PRF service — hiker profile logic.
"""

import pytest

from app.modules.prf.schemas import FitnessLevel, HikerProfile
from app.modules.prf.service import (
    default_profile,
    fitness_percentile,
    validate_profile,
    velocity_factor,
)


class TestValidateProfile:
    def test_valid_profile(self):
        p = HikerProfile(weight_kg=70, load_kg=10, fitness_level=FitnessLevel.MEDIUM)
        assert validate_profile(p) == p

    def test_default_profile_values(self):
        p = default_profile()
        assert p.weight_kg == 70.0
        assert p.load_kg == 10.0
        assert p.fitness_level == FitnessLevel.MEDIUM


class TestFitnessPercentile:
    def test_low_is_25(self):
        assert fitness_percentile(FitnessLevel.LOW) == 0.25

    def test_athlete_is_95(self):
        assert fitness_percentile(FitnessLevel.ATHLETE) == 0.95


class TestVelocityFactor:
    def test_athlete_fastest(self):
        assert velocity_factor(
            HikerProfile(fitness_level=FitnessLevel.ATHLETE)
        ) == pytest.approx(1.30)

    def test_low_slowest(self):
        assert velocity_factor(
            HikerProfile(fitness_level=FitnessLevel.LOW)
        ) == pytest.approx(0.70)

    def test_medium_is_baseline(self):
        assert velocity_factor(
            HikerProfile(fitness_level=FitnessLevel.MEDIUM)
        ) == pytest.approx(1.00)

    def test_profile_validation_rejects_load_ge_weight(self):
        with pytest.raises(ValueError):
            HikerProfile(weight_kg=70, load_kg=70)
