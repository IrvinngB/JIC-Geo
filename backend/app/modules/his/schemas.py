"""Pydantic schemas for route history endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, field_validator


class HistoryCreate(BaseModel):
    route_name: str | None = None
    route_id: str
    source_format: str | None = None
    profile_id: str | None = None
    analysis_json: str  # serialized JSON string


class HistorySummary(BaseModel):
    id: str
    route_name: str | None
    route_id: str
    source_format: str | None
    is_favorite: bool
    mide_global: int | None
    total_distance_km: float | None
    estimated_time_h: float | None
    total_kcal: float | None
    elevation_gain_m: float | None
    risk_max: int | None
    created_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("id", mode="before")
    @classmethod
    def convert_uuid(cls, v):
        return str(v) if isinstance(v, UUID) else v


class HistoryDetail(HistorySummary):
    profile_id: str | None
    analysis_json: str

    @field_validator("profile_id", mode="before")
    @classmethod
    def convert_profile_uuid(cls, v):
        return str(v) if isinstance(v, UUID) else v


class HistoryUpdateFavorite(BaseModel):
    is_favorite: bool
