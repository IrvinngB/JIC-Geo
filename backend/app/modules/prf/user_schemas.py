"""Pydantic schemas for user-facing profile CRUD (separate from biomechanical PRF schemas)."""

from datetime import datetime

from pydantic import BaseModel, field_validator


class UserProfileCreate(BaseModel):
    name: str
    weight_kg: float
    load_kg: float = 0
    fitness_level: str = "medium"
    surface_type: str = "dirt"

    @field_validator("fitness_level")
    @classmethod
    def validate_fitness(cls, v: str) -> str:
        if v not in ("low", "medium", "high", "athlete"):
            raise ValueError("fitness_level must be low, medium, high, or athlete")
        return v

    @field_validator("surface_type")
    @classmethod
    def validate_surface(cls, v: str) -> str:
        valid = ("dirt", "paved", "gravel", "mud", "sand", "scrub", "dense_scrub")
        if v not in valid:
            raise ValueError(f"surface_type must be one of {valid}")
        return v

    @field_validator("weight_kg")
    @classmethod
    def validate_weight(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("weight_kg must be positive")
        return v

    @field_validator("load_kg")
    @classmethod
    def validate_load(cls, v: float) -> float:
        if v < 0:
            raise ValueError("load_kg cannot be negative")
        return v


class UserProfileUpdate(BaseModel):
    name: str | None = None
    weight_kg: float | None = None
    load_kg: float | None = None
    fitness_level: str | None = None
    surface_type: str | None = None


class UserProfileResponse(BaseModel):
    id: str
    name: str
    weight_kg: float
    load_kg: float
    fitness_level: str
    surface_type: str
    is_default: bool
    created_at: datetime

    model_config = {"from_attributes": True}
