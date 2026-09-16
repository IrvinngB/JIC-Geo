"""Pydantic schemas for share endpoints."""

from datetime import datetime

from pydantic import BaseModel, field_validator
from uuid import UUID


class ShareCreate(BaseModel):
    history_id: str


class ShareResponse(BaseModel):
    id: str
    share_code: str
    url: str
    created_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("id", mode="before")
    @classmethod
    def convert_uuid(cls, v):
        return str(v) if isinstance(v, UUID) else v


class SharedRoutePublic(BaseModel):
    route_name: str | None
    mide_global: int | None
    total_distance_km: float | None
    estimated_time_h: float | None
    total_kcal: float | None
    elevation_gain_m: float | None
    analysis_json: str
    created_at: datetime
    view_count: int
