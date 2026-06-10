"""
RUT schemas — input/output contracts for route processing.
"""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class RouteProcessRequest(BaseModel):
    """Optional parameters for route re-processing."""

    segment_length_m: float = Field(default=100.0, gt=0, description="RUT-01")
    savgol_window: int = Field(default=5, ge=5, le=21, description="RUT-09")


class SegmentProcessedOut(BaseModel):
    """Segment summary after RUT processing."""

    seq: int
    length_m: float
    elevation_start: float
    elevation_end: float
    slope_pct: float
    direction: str  # 'ascent' | 'descent'

    model_config = {"from_attributes": True}


class RouteProcessResponse(BaseModel):
    """Response returned after processing a route through the RUT pipeline."""

    route_id: uuid.UUID
    segment_count: int
    total_length_m: float
    elevation_gain_m: float
    elevation_loss_m: float
    points_corrected: int
    dem_source: str | None
    segments: list[SegmentProcessedOut]
