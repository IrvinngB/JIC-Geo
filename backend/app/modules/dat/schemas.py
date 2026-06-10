"""
Pydantic schemas for DAT — route ingestion and spatial data.
These are the output contracts; downstream modules depend on these types.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from pydantic import BaseModel, Field


class SegmentOut(BaseModel):
    """Summary of a single route segment after ingestion."""

    id: int
    seq: int
    length_m: float | None
    elevation_start: float | None
    elevation_end: float | None
    slope_pct: float | None
    surface_type: str
    canopy_density: float

    model_config = {"from_attributes": True}


class RouteUploadResponse(BaseModel):
    """Response returned after a successful route upload."""

    route_id: uuid.UUID
    name: str | None
    source_format: str
    segment_count: int
    total_length_m: Annotated[float, Field(description="Sum of all segment lengths in metres")]
    segments: list[SegmentOut]


class RouteOut(BaseModel):
    """Full route representation with its segments."""

    id: uuid.UUID
    name: str | None
    source_format: str
    uploaded_at: str
    segment_count: int
    total_length_m: float
    segments: list[SegmentOut]

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# DEM schemas (DAT-04, DAT-09, DAT-10)
# ---------------------------------------------------------------------------


class DEMSourceOut(BaseModel):
    """DEM source entry as returned by the registry."""

    id: int
    name: str
    resolution_m: float
    priority: int
    rast_table: str

    model_config = {"from_attributes": True}


class DEMUploadResponse(BaseModel):
    """Response returned after a successful DEM upload."""

    dem_source: DEMSourceOut
    tile_count: Annotated[int, Field(description="Number of 100×100 px tiles inserted")]
