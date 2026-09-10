"""History endpoints — CRUD for route analysis history."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.models import User
from app.db.session import get_db
from app.modules.his.schemas import HistoryCreate, HistoryDetail, HistorySummary, HistoryUpdateFavorite
from app.modules.his.service import (
    count_history,
    create_history,
    delete_history,
    get_history,
    list_history,
    toggle_favorite,
)

router = APIRouter()


@router.post("", response_model=HistorySummary, status_code=status.HTTP_201_CREATED)
async def save_analysis(
    body: HistoryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    record = await create_history(
        db,
        user_id=current_user.id,
        route_name=body.route_name,
        route_id=body.route_id,
        source_format=body.source_format,
        profile_id=body.profile_id,
        analysis_json=body.analysis_json,
    )
    return record


@router.get("")
async def get_history_list(
    favorites_only: bool = Query(False),
    search: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items = await list_history(db, current_user.id, favorites_only, search, limit, offset)
    total = await count_history(db, current_user.id)
    return {
        "items": [HistorySummary.model_validate(i) for i in items],
        "total": total,
    }


@router.get("/{history_id}", response_model=HistoryDetail)
async def get_history_detail(
    history_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    record = await get_history(db, current_user.id, history_id)
    if not record:
        raise HTTPException(status_code=404, detail="History not found")
    return record


@router.delete("/{history_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_history(
    history_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    deleted = await delete_history(db, current_user.id, history_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="History not found")


@router.put("/{history_id}/favorite", response_model=HistorySummary)
async def update_favorite(
    history_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    record = await toggle_favorite(db, current_user.id, history_id)
    if not record:
        raise HTTPException(status_code=404, detail="History not found")
    return record
