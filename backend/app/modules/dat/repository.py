"""
DAT repository — spatial persistence layer.
Handles all DB writes for Route + Segment records.
Never raises domain errors; let the service layer handle that.
"""

from __future__ import annotations

import uuid

from geoalchemy2.shape import from_shape
from shapely.geometry import LineString, mapping
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Route, Segment


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


async def get_route(db: AsyncSession, route_id: uuid.UUID) -> Route | None:
    """Fetch a Route with its segments by primary key."""
    result = await db.execute(
        select(Route)
        .where(Route.id == route_id)
        .options(selectinload(Route.segments))
    )
    return result.scalar_one_or_none()
