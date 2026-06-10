"""
DAT router — route and DEM ingestion endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.dat import repository as dat_repo
from app.modules.dat import service as dat_service
from app.modules.dat.schemas import DEMSourceOut, DEMUploadResponse, RouteOut, RouteUploadResponse, SegmentOut
from app.db.models import Route

# ---------------------------------------------------------------------------
# Routes router
# ---------------------------------------------------------------------------

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


@router.get("/{route_id}", response_model=RouteOut)
async def get_route(
    route_id: str,
    db: AsyncSession = Depends(get_db),
) -> RouteOut:
    """
    Retrieve a persisted route by its UUID, including all segments.
    """
    from uuid import UUID
    try:
        route_uuid = UUID(route_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid route_id format. Must be a valid UUID.",
        )

    route = await dat_repo.get_route(db, route_uuid)
    if route is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Route '{route_id}' not found.",
        )

    segments_out = [
        SegmentOut.model_validate(seg)
        for seg in sorted(route.segments, key=lambda s: s.seq)
    ]
    total_length = sum(s.length_m for s in route.segments if s.length_m is not None)

    return RouteOut(
        id=route.id,
        name=route.name,
        source_format=route.source_format,
        uploaded_at=str(route.uploaded_at),
        segment_count=len(segments_out),
        total_length_m=round(total_length, 1),
        segments=segments_out,
    )


@router.get("/{route_id}/segments", response_model=list[SegmentOut])
async def get_route_segments(
    route_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[SegmentOut]:
    """
    Get all segments of a route with their attributes (API-05).
    """
    from uuid import UUID
    try:
        route_uuid = UUID(route_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid route_id format. Must be a valid UUID.",
        )

    route = await dat_repo.get_route(db, route_uuid)
    if route is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Route '{route_id}' not found.",
        )

    return [
        SegmentOut.model_validate(seg)
        for seg in sorted(route.segments, key=lambda s: s.seq)
    ]


# ---------------------------------------------------------------------------
# DEM router (DAT-04, DAT-09, DAT-10)
# ---------------------------------------------------------------------------

dem_router = APIRouter()


@dem_router.post("/upload", response_model=DEMUploadResponse, status_code=201)
async def upload_dem(
    file: UploadFile = File(..., description="GeoTIFF DEM file (.tif / .tiff)"),
    name: str = Form(..., description="Unique identifier for this DEM source"),
    resolution_m: float = Form(..., gt=0, description="Native spatial resolution in metres"),
    priority: int = Form(default=0, description="Higher value = preferred when DEMs overlap (DAT-10)"),
    db: AsyncSession = Depends(get_db),
) -> DEMUploadResponse:
    """
    Upload a GeoTIFF DEM and register it as a queryable PostGIS raster source.

    - Validates the file is a GeoTIFF (magic bytes check).
    - Creates a dedicated raster table named after the DEM.
    - Tiles the raster at 100×100 px for efficient spatial queries.
    - Adds a GIST index on ST_ConvexHull(rast).
    - Registers metadata in the dem_sources registry (DAT-09, DAT-10).
    """
    raw = await dat_service.read_and_validate_dem(file)
    rast_table = dat_service.make_dem_table_name(name)

    try:
        source, tile_count = await dat_repo.save_dem(
            db,
            name=name,
            rast_table=rast_table,
            resolution_m=resolution_m,
            priority=priority,
            file_bytes=raw,
        )
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A DEM source named '{name}' already exists.",
        )

    return DEMUploadResponse(
        dem_source=DEMSourceOut.model_validate(source),
        tile_count=tile_count,
    )


@dem_router.get("/sources", response_model=list[DEMSourceOut])
async def list_dem_sources(
    db: AsyncSession = Depends(get_db),
) -> list[DEMSourceOut]:
    """
    List all registered DEM sources (DAT-10).
    """
    sources = await dat_repo.list_dem_sources(db)
    return [DEMSourceOut.model_validate(s) for s in sources]
