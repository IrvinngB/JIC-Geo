"""
RUT repository — spatial queries for route processing.
All database I/O lives here; no business logic.
"""

from __future__ import annotations

import uuid

from geoalchemy2.shape import from_shape
from shapely.geometry import LineString
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import DEMSource, Route, Segment


async def get_route_with_segments(db: AsyncSession, route_id: uuid.UUID) -> Route | None:
    """Fetch a Route eagerly loading its segments."""
    result = await db.execute(
        select(Route)
        .where(Route.id == route_id)
        .options(selectinload(Route.segments))
    )
    return result.scalar_one_or_none()


async def get_route_coords(db: AsyncSession, route_id: uuid.UUID) -> list[tuple[float, float, float]]:
    """
    Extract ordered (lon, lat, elev) coordinates from a Route's LINESTRINGZ.
    Uses ST_DumpPoints to preserve order.
    """
    result = await db.execute(
        text(
            """
            SELECT
                ST_X(dmp.geom) AS lon,
                ST_Y(dmp.geom) AS lat,
                ST_Z(dmp.geom) AS elev
            FROM routes, ST_DumpPoints(geom) AS dmp
            WHERE id = :route_id
            ORDER BY dmp.path
            """
        ),
        {"route_id": str(route_id)},
    )
    rows = result.fetchall()
    return [(row.lon, row.lat, row.elev) for row in rows]


async def get_best_dem_source(db: AsyncSession) -> DEMSource | None:
    """Return the highest-priority DEM source, or None if none registered."""
    result = await db.execute(
        select(DEMSource).order_by(DEMSource.priority.desc()).limit(1)
    )
    return result.scalar_one_or_none()


async def get_dem_elevations(
    db: AsyncSession,
    coords: list[tuple[float, float, float]],
    rast_table: str,
) -> list[float | None]:
    """
    Query PostGIS raster for elevation at each coordinate.
    RUT-08: Uses Bilinear resampling.

    Parameters
    ----------
    coords: list of (lon, lat, elev)
    rast_table: sanitized table name (from dat_service.make_dem_table_name)

    Returns
    -------
    list of float | None, same length as coords.
    """
    values: list[float | None] = []
    for lon, lat, _ in coords:
        result = await db.execute(
            text(
                f"""
                SELECT ST_Value(
                    rast,
                    ST_SetSRID(ST_MakePoint(:lon, :lat), 4326),
                    resample := 'Bilinear'
                ) AS elev
                FROM {rast_table}
                WHERE ST_Intersects(
                    rast,
                    ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)
                )
                LIMIT 1
                """
            ),
            {"lon": lon, "lat": lat},
        )
        row = result.mappings().one_or_none()
        values.append(row["elev"] if row else None)
    return values


async def replace_segments(
    db: AsyncSession,
    route_id: uuid.UUID,
    segments_data: list[dict],
    dem_source: DEMSource | None = None,
) -> None:
    """
    Delete existing segments for a route and insert the newly processed ones.
    """
    # Delete old segments
    await db.execute(
        text("DELETE FROM segments WHERE route_id = :route_id"),
        {"route_id": str(route_id)},
    )

    # Insert new segments
    for seg in segments_data:
        await db.execute(
            text(
                """
                INSERT INTO segments (
                    route_id, seq, geom, length_m,
                    elevation_start, elevation_end, slope_pct,
                    dem_source, dem_resolution_m, elevation_interpolated
                )
                VALUES (
                    :route_id, :seq, ST_SetSRID(ST_GeomFromText(:geom_wkt), 4326),
                    :length_m, :elevation_start, :elevation_end, :slope_pct,
                    :dem_source, :dem_resolution_m, :elevation_interpolated
                )
                """
            ),
            {
                "route_id": str(route_id),
                "seq": seg["seq"],
                "geom_wkt": seg["geom_wkt"],
                "length_m": seg["length_m"],
                "elevation_start": seg["elevation_start"],
                "elevation_end": seg["elevation_end"],
                "slope_pct": seg["slope_pct"],
                "dem_source": dem_source.name if dem_source else None,
                "dem_resolution_m": dem_source.resolution_m if dem_source else None,
                "elevation_interpolated": seg.get("elevation_interpolated", False),
            },
        )


async def get_segments_for_route(
    db: AsyncSession,
    route_id: uuid.UUID,
) -> list[Segment]:
    """Return all segments for a route ordered by seq."""
    result = await db.execute(
        select(Segment)
        .where(Segment.route_id == route_id)
        .order_by(Segment.seq)
    )
    return list(result.scalars().all())
