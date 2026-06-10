"""
RUT router — route processing endpoints.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.rut import repository as rut_repo
from app.modules.rut import service as rut_service
from app.modules.rut.schemas import RouteProcessRequest, RouteProcessResponse, SegmentProcessedOut

router = APIRouter()


@router.post("/{route_id}/process", response_model=RouteProcessResponse)
async def process_route(
    route_id: str,
    payload: RouteProcessRequest = RouteProcessRequest(),
    db: AsyncSession = Depends(get_db),
) -> RouteProcessResponse:
    """
    Re-process a route through the RUT pipeline.

    1. Extract raw coordinates from the stored route.
    2. If a DEM is available, sample elevations via bilinear interpolation.
    3. Detect and repair elevation spikes.
    4. Apply Savitzky-Golay smoothing.
    5. Re-segment and recalculate gradients.
    6. Persist new segments, replacing old ones.
    """
    try:
        route_uuid = uuid.UUID(route_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid route_id format. Must be a valid UUID.",
        )

    route = await rut_repo.get_route_with_segments(db, route_uuid)
    if route is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Route '{route_id}' not found.",
        )

    # 1. Extract coords
    coords = await rut_repo.get_route_coords(db, route_uuid)
    if len(coords) < 2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Route must contain at least 2 points.",
        )

    # 2. DEM
    dem_source = await rut_repo.get_best_dem_source(db)
    dem_values = None
    if dem_source:
        dem_values = await rut_repo.get_dem_elevations(db, coords, dem_source.rast_table)

    # 3–5. Pure pipeline
    result = rut_service.process_route_pipeline(
        coords,
        dem_values=dem_values,
        segment_length_m=payload.segment_length_m,
        window=payload.savgol_window,
    )

    # 6. Persist
    await rut_repo.replace_segments(db, route_uuid, result["segments"], dem_source)
    await db.commit()

    # Re-load segments with their DB IDs for the response
    segments_db = await rut_repo.get_segments_for_route(db, route_uuid)
    segments_out = [
        SegmentProcessedOut(
            seq=seg.seq,
            length_m=seg.length_m or 0.0,
            elevation_start=seg.elevation_start or 0.0,
            elevation_end=seg.elevation_end or 0.0,
            slope_pct=seg.slope_pct or 0.0,
            direction="ascent" if (seg.slope_pct or 0) > 0 else "descent",
        )
        for seg in segments_db
    ]

    total_length = sum(s.length_m for s in segments_db if s.length_m is not None)

    return RouteProcessResponse(
        route_id=route_uuid,
        segment_count=len(segments_out),
        total_length_m=round(total_length, 1),
        elevation_gain_m=round(result["elevation_gain_m"], 1),
        elevation_loss_m=round(result["elevation_loss_m"], 1),
        points_corrected=result["points_corrected"],
        dem_source=dem_source.name if dem_source else None,
        segments=segments_out,
    )
