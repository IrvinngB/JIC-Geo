"""GPS Tracking endpoints — save and retrieve recorded tracks."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.track.schemas import TrackSave, TrackResponse
from app.modules.track.service import save_track, get_track_by_history

router = APIRouter()


@router.post("", response_model=TrackResponse)
async def save_gps_track(
    body: TrackSave,
    db: AsyncSession = Depends(get_db),
):
    history_id = UUID(body.history_id)
    track = await save_track(
        db,
        history_id=history_id,
        coordinates=body.coordinates,
        total_distance_m=body.total_distance_m,
        duration_s=body.duration_s,
        avg_speed_kmh=body.avg_speed_kmh,
    )
    if not track:
        raise HTTPException(status_code=404, detail="History not found")
    return track


@router.get("/{history_id}", response_model=TrackResponse)
async def get_gps_track(
    history_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    track = await get_track_by_history(db, history_id)
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    return track
