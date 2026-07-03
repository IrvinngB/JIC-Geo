"""
Pydantic schemas for DAT — route ingestion and spatial data.
These are the output contracts; downstream modules depend on these types.
"""

from __future__ import annotations

import uuid
from typing import Annotated, Literal

from pydantic import BaseModel, Field, model_validator

# Canonical surface types (DAT-07). Must stay in sync with TERRAIN_ETA keys
# in app.modules.met.service — met is downstream, so it cannot be imported here.
SurfaceType = Literal[
    "asphalt",
    "pavement",
    "dirt",
    "scrub",
    "dense_scrub",
    "sand_mud",
    "mud",
    "sand",
]


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
    elevation_interpolated: bool = False

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


class SegmentSurfacePatch(BaseModel):
    """Manual override of terrain attributes for a range of segments (DAT-07, DAT-08)."""

    surface_type: SurfaceType | None = None
    canopy_density: float | None = Field(default=None, ge=0.0, le=1.0)
    seq_from: int | None = Field(
        default=None, ge=0, description="First segment seq to update (inclusive). Omit for whole route."
    )
    seq_to: int | None = Field(
        default=None, ge=0, description="Last segment seq to update (inclusive). Omit for whole route."
    )

    @model_validator(mode="after")
    def validate_patch(self) -> "SegmentSurfacePatch":
        if self.surface_type is None and self.canopy_density is None:
            raise ValueError("At least one of surface_type or canopy_density is required")
        if self.seq_from is not None and self.seq_to is not None and self.seq_from > self.seq_to:
            raise ValueError("seq_from must be <= seq_to")
        return self


class SegmentSurfacePatchResponse(BaseModel):
    """Response after a terrain attribute override."""

    route_id: uuid.UUID
    updated_count: int
    segments: list[SegmentOut]


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
