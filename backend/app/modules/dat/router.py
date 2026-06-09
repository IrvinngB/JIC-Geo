"""
DAT router — route ingestion endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.dat import repository as dat_repo
from app.modules.dat import service as dat_service
from app.modules.dat.schemas import RouteUploadResponse, SegmentOut

router = APIRouter()


@router.post("/upload", response_model=RouteUploadResponse, status_code=201)
async def upload_route(
    file: UploadFile = File(..., description="GPX or GeoJSON route file"),
    db: AsyncSession = Depends(get_db),
) -> RouteUploadResponse:
    """
    Upload a GPX or GeoJSON route file.

    - Parses coordinates and splits the route into 100 m segments.
    - Persists the full 3DZ LineString geometry and segment metadata.
    - Returns the route ID, segment count, and per-segment summary.
    """
    parsed = await dat_service.parse_upload(file)

    route = await dat_repo.save_route(
        db,
        name=parsed["name"],
        source_format=parsed["source_format"],
        geom_wkt=parsed["geom_wkt"],
        segments_data=parsed["segments_data"],
    )

    segments_out = [
        SegmentOut.model_validate(seg)
        for seg in sorted(route.segments, key=lambda s: s.seq)
    ]

    total_length = sum(s.length_m for s in route.segments if s.length_m is not None)

    return RouteUploadResponse(
        route_id=route.id,
        name=route.name,
        source_format=route.source_format,
        segment_count=len(segments_out),
        total_length_m=round(total_length, 1),
        segments=segments_out,
    )
