"""Pydantic schemas for CLI — climate integration."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


ClimateSource = Literal["api", "simulation", "forecast"]


class ClimateData(BaseModel):
    """Normalized climate data used by CLI/RIE/GRF. CLI-08, SIM-02."""

    temperature_c: float
    humidity_pct: float = Field(ge=0, le=100)
    precip_mm: float = Field(ge=0)
    uv_index: float = Field(ge=0)
    wbgt: float
    source: ClimateSource
    timestamp: datetime
    zone_id: str | None = None
    # Kept so WBGT can be recomputed after elevation-based temperature adjustment.
    shortwave_radiation_w_m2: float | None = None


class ClimateTimeline(BaseModel):
    """Hourly climate along a hike, indexed by whole hours after `start`. CLI-10.

    `reference_elevation_m` is the elevation of the forecast grid point; segments
    at a different elevation get a lapse-rate temperature correction.
    """

    start: datetime
    hours: list[ClimateData] = Field(min_length=1)
    reference_elevation_m: float | None = None


class ClimateCurrentResponse(ClimateData):
    """Response for GET /climate/current. API-07."""

    lat: float
    lon: float
    cached: bool = False


class ClimateOverride(BaseModel):
    """Manual simulation climate override. SIM-01."""

    temperature_c: float
    humidity_pct: float = Field(ge=0, le=100)
    precip_mm: float = Field(default=0, ge=0)
    uv_index: float = Field(default=0, ge=0)
