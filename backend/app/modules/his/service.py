"""History service — CRUD for route analysis history."""

import json
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import RouteHistory


async def create_history(
    db: AsyncSession,
    user_id: UUID,
    route_name: str | None,
    route_id: str,
    source_format: str | None,
    profile_id: str | None,
    analysis_json: str,
) -> RouteHistory:
    # Parse analysis_json to extract summary fields
    try:
        analysis = json.loads(analysis_json)
        summary = analysis.get("summary", {})
    except (json.JSONDecodeError, AttributeError):
        summary = {}

    record = RouteHistory(
        user_id=user_id,
        profile_id=UUID(profile_id) if profile_id else None,
        route_name=route_name,
        route_id=route_id,
        source_format=source_format,
        mide_global=summary.get("mide_global"),
        total_distance_km=summary.get("total_distance_km"),
        estimated_time_h=summary.get("estimated_time_h"),
        total_kcal=summary.get("total_kcal"),
        elevation_gain_m=summary.get("elevation_gain_m"),
        risk_max=summary.get("risk_max"),
        analysis_json=analysis_json,
    )
    db.add(record)
    await db.flush()
    await db.refresh(record)
    return record


async def list_history(
    db: AsyncSession,
    user_id: UUID,
    favorites_only: bool = False,
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[RouteHistory]:
    query = select(RouteHistory).where(RouteHistory.user_id == user_id)

    if favorites_only:
        query = query.where(RouteHistory.is_favorite == True)

    if search:
        query = query.where(RouteHistory.route_name.ilike(f"%{search}%"))

    query = query.order_by(RouteHistory.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_history(db: AsyncSession, user_id: UUID, history_id: UUID) -> RouteHistory | None:
    result = await db.execute(
        select(RouteHistory).where(
            RouteHistory.id == history_id,
            RouteHistory.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def delete_history(db: AsyncSession, user_id: UUID, history_id: UUID) -> bool:
    record = await get_history(db, user_id, history_id)
    if not record:
        return False
    await db.delete(record)
    return True


async def toggle_favorite(db: AsyncSession, user_id: UUID, history_id: UUID) -> RouteHistory | None:
    record = await get_history(db, user_id, history_id)
    if not record:
        return None
    record.is_favorite = not record.is_favorite
    await db.flush()
    await db.refresh(record)
    return record


async def count_history(db: AsyncSession, user_id: UUID) -> int:
    result = await db.execute(
        select(func.count()).select_from(RouteHistory).where(RouteHistory.user_id == user_id)
    )
    return result.scalar() or 0
