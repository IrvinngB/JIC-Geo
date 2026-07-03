"""
DAT repository — spatial persistence layer.
Handles all DB writes for Route + Segment records.
Never raises domain errors; let the service layer handle that.
"""

from __future__ import annotations

import uuid

from geoalchemy2.shape import from_shape
from shapely.geometry import LineString, mapping
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import DEMSource, Route, Segment


async def save_route(
    db: AsyncSession,
    *,
    name: str | None,
    source_format: str,
    geom_wkt: str,
    segments_data: list[dict],
) -> Route:
    """
    Persist a Route and its Segments in a single transaction.

    Parameters
    ----------
    db:
        Active async session (commit is handled by the FastAPI dependency).
    name:
        Human-readable route name (from GPX track name or GeoJSON property).
    source_format:
        'gpx' | 'geojson'
    geom_wkt:
        WKT representation of the full 3DZ LineString (SRID 4326).
    segments_data:
        List of dicts with keys: seq, geom_wkt, length_m,
        elevation_start, elevation_end, slope_pct.

    Returns
    -------
    Route:
        The persisted Route ORM object with segments eagerly loaded.
    """
    route = Route(
        id=uuid.uuid4(),
        name=name,
        source_format=source_format,
        geom=f"SRID=4326;{geom_wkt}",
    )
    db.add(route)
    await db.flush()  # get route.id without committing

    segments = [
        Segment(
            route_id=route.id,
            seq=seg["seq"],
            geom=f"SRID=4326;{seg['geom_wkt']}",
            length_m=seg.get("length_m"),
            elevation_start=seg.get("elevation_start"),
            elevation_end=seg.get("elevation_end"),
            slope_pct=seg.get("slope_pct"),
        )
        for seg in segments_data
    ]
    db.add_all(segments)
    await db.flush()

    # Reload with relationships to build the response
    result = await db.execute(
        select(Route)
        .where(Route.id == route.id)
        .options(selectinload(Route.segments))
    )
    return result.scalar_one()


async def list_dem_sources(db: AsyncSession) -> list[DEMSource]:
    """Fetch all registered DEM sources ordered by priority (highest first)."""
    from sqlalchemy import select
    result = await db.execute(
        select(DEMSource).order_by(DEMSource.priority.desc())
    )
    return list(result.scalars().all())


async def get_route(db: AsyncSession, route_id: uuid.UUID) -> Route | None:
    """Fetch a Route with its segments by primary key."""
    result = await db.execute(
        select(Route)
        .where(Route.id == route_id)
        .options(selectinload(Route.segments))
    )
    return result.scalar_one_or_none()


async def save_dem(
    db: AsyncSession,
    *,
    name: str,
    rast_table: str,
    resolution_m: float,
    priority: int,
    file_bytes: bytes,
) -> tuple[DEMSource, int]:
    """
    Create a PostGIS raster table, load the DEM tiles, and register the source.

    The raster table is created dynamically at runtime — one table per DEM source.
    This is an intentional exception to the Alembic-only rule: these tables are
    data-bearing (populated from user uploads), not fixed schema changes.

    Parameters
    ----------
    name:
        Human-readable identifier (must be unique in dem_sources).
    rast_table:
        SQL-safe table name produced by dat_service.make_dem_table_name().
    resolution_m:
        Native resolution of the source DEM in metres (metadata only).
    priority:
        Higher value = preferred when multiple DEMs overlap (DAT-10).
    file_bytes:
        Raw GeoTIFF bytes.  PostGIS parses them via ST_FromGDALRaster (GDAL).

    Returns
    -------
    (DEMSource ORM object, tile_count)
    """
    # Create the raster table. table name is sanitised by make_dem_table_name(),
    # so f-string interpolation here is safe.
    await db.execute(text(
        f"CREATE TABLE IF NOT EXISTS {rast_table} "
        "(rid SERIAL PRIMARY KEY, rast RASTER)"
    ))

    # Tile the raster at DEM_TILE_SIZE_PX × DEM_TILE_SIZE_PX and insert.
    # ST_FromGDALRaster accepts the raw file bytes as bytea (asyncpg converts
    # Python bytes → bytea automatically).
    result = await db.execute(
        text(
            f"INSERT INTO {rast_table} (rast) "
            "SELECT ST_Tile(ST_FromGDALRaster(:rb), 100, 100) "
            "RETURNING rid"
        ),
        {"rb": file_bytes},
    )
    tile_count = len(result.fetchall())

    # Spatial index on the convex hull of each tile (standard PostGIS pattern).
    await db.execute(text(
        f"CREATE INDEX IF NOT EXISTS idx_{rast_table}_rast "
        f"ON {rast_table} USING GIST(ST_ConvexHull(rast))"
    ))

    source = DEMSource(
        name=name,
        resolution_m=resolution_m,
        priority=priority,
        rast_table=rast_table,
    )
    db.add(source)
    await db.flush()

    return source, tile_count
