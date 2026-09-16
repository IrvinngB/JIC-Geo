"""GPS Track service — save and retrieve recorded tracks."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from geoalchemy2.shape import from_shape
from shapely.geometry import LineString

from app.db.models import GpsTrack, RouteHistory


async def save_track(
    db: AsyncSession,
    history_id: UUID,
    coordinates: list[list[float]],
    total_distance_m: float | None,
    duration_s: int | None,
    avg_speed_kmh: float | None,
) -> GpsTrack | None:
    # Verify history exists
    result = await db.execute(
        select(RouteHistory).where(RouteHistory.id == history_id)
    )
    if not result.scalar_one_or_none():
        return None

    # Build LineString from coordinates [[lng, lat, alt], ...]
    line = LineString(coordinates)
    geom = from_shape(line, srid=4326)

    track = GpsTrack(
        history_id=history_id,
        geom=geom,
        total_distance_m=total_distance_m,
        duration_s=duration_s,
        avg_speed_kmh=avg_speed_kmh,
    )
    db.add(track)
    await db.flush()
    await db.refresh(track)
    return track


async def get_track_by_history(db: AsyncSession, history_id: UUID) -> GpsTrack | None:
    result = await db.execute(
        select(GpsTrack).where(GpsTrack.history_id == history_id)
    )
    return result.scalar_one_or_none()
