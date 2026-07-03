"""
PRF — Hiker profile service.
Pure business logic: no database calls.
PRF-01 to PRF-06.
"""

from __future__ import annotations

from app.modules.prf.schemas import FITNESS_PERCENTILE, FitnessLevel, HikerProfile


def validate_profile(profile: HikerProfile) -> HikerProfile:
    """
    Validate and return a hiker profile.
    Pydantic already enforces PRF-01 to PRF-06; this function is a thin
    wrapper that allows downstream modules to depend on a service layer
    rather than importing schemas directly.
    """
    return profile


def default_profile() -> HikerProfile:
    """Return the default hiker profile (PRF-05)."""
    return HikerProfile()


def fitness_percentile(level: FitnessLevel) -> float:
    """PRF-04: Map fitness level to a percentile for Lorentz curve selection."""
    return FITNESS_PERCENTILE[level]


def velocity_factor(profile: HikerProfile) -> float:
    """
    Apply a velocity factor based on fitness level.
    Simplified Lorentz curve mapping:
      - Low      → 0.70
      - Medium   → 1.00
      - High     → 1.15
      - Athlete  → 1.30
    """
    factors = {
        FitnessLevel.LOW: 0.70,
        FitnessLevel.MEDIUM: 1.00,
        FitnessLevel.HIGH: 1.15,
        FitnessLevel.ATHLETE: 1.30,
    }
    return factors[profile.fitness_level]
