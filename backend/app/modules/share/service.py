"""Share service — create and retrieve public shared routes."""

import secrets
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import RouteHistory, SharedRoute


def generate_share_code() -> str:
    """Generate a short, URL-safe share code."""
    return secrets.token_urlsafe(6)[:8]


async def create_share(
    db: AsyncSession,
    history_id: UUID,
    user_id: UUID,
) -> SharedRoute | None:
    # Verify the history belongs to the user
    result = await db.execute(
        select(RouteHistory).where(
            RouteHistory.id == history_id,
            RouteHistory.user_id == user_id,
        )
    )
    history = result.scalar_one_or_none()
    if not history:
        return None

    # Check if already shared
    existing = await db.execute(
        select(SharedRoute).where(SharedRoute.history_id == history_id)
    )
    existing_share = existing.scalar_one_or_none()
    if existing_share:
        return existing_share

    share = SharedRoute(
        history_id=history_id,
        share_code=generate_share_code(),
        created_by=user_id,
    )
    db.add(share)
    await db.flush()
    await db.refresh(share)
    return share


async def get_shared_by_code(db: AsyncSession, code: str) -> tuple[SharedRoute, RouteHistory] | None:
    result = await db.execute(
        select(SharedRoute, RouteHistory).join(
            RouteHistory, SharedRoute.history_id == RouteHistory.id
        ).where(SharedRoute.share_code == code)
    )
    row = result.first()
    if not row:
        return None

    share, history = row
    # Increment view count
    await db.execute(
        update(SharedRoute)
        .where(SharedRoute.id == share.id)
        .values(view_count=SharedRoute.view_count + 1)
    )
    await db.flush()
    return share, history
