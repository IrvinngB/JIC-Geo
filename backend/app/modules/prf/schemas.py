"""
PRF — Hiker profile schemas.
PRF-01 to PRF-06.
"""

from enum import StrEnum

from pydantic import BaseModel, Field, model_validator


class FitnessLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ATHLETE = "athlete"


# Percentile mapping for Lorentz curve selection (PRF-04)
FITNESS_PERCENTILE: dict[FitnessLevel, float] = {
    FitnessLevel.LOW: 0.25,
    FitnessLevel.MEDIUM: 0.50,
    FitnessLevel.HIGH: 0.75,
    FitnessLevel.ATHLETE: 0.95,
}


class HikerProfile(BaseModel):
    """Input profile for a hiker — PRF-01 to PRF-05."""

    weight_kg: float = Field(default=70.0, gt=0, description="Body weight in kg")
    load_kg: float = Field(default=10.0, ge=0, description="External load (backpack) in kg")
    fitness_level: FitnessLevel = Field(default=FitnessLevel.MEDIUM)

    @model_validator(mode="after")
    def load_must_be_less_than_weight(self) -> "HikerProfile":
        """PRF-06: load < weight."""
        if self.load_kg >= self.weight_kg:
            raise ValueError("load_kg must be less than weight_kg")
        return self

    @property
    def fitness_percentile(self) -> float:
        return FITNESS_PERCENTILE[self.fitness_level]
