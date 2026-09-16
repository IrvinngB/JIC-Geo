"""Pydantic schemas for GPS tracking endpoints."""

from datetime import datetime
from pydantic import BaseModel, field_validator
from uuid import UUID


class TrackSave(BaseModel):
    history_id: str
    coordinates: list[list[float]]  # [[lng, lat, alt], ...]
    total_distance_m: float | None = None
    duration_s: int | None = None
    avg_speed_kmh: float | None = None


class TrackResponse(BaseModel):
    id: str
    history_id: str
    total_distance_m: float | None
    duration_s: int | None
    avg_speed_kmh: float | None
    recorded_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("id", "history_id", mode="before")
    @classmethod
    def convert_uuid(cls, v):
        return str(v) if isinstance(v, UUID) else v
