"""User profile service — CRUD for hiker profiles (separate from biomechanical PRF service)."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Profile


async def list_profiles(db: AsyncSession, user_id: UUID) -> list[Profile]:
    result = await db.execute(
        select(Profile).where(Profile.user_id == user_id).order_by(Profile.created_at.desc())
    )
    return list(result.scalars().all())


async def get_profile(db: AsyncSession, user_id: UUID, profile_id: UUID) -> Profile | None:
    result = await db.execute(
        select(Profile).where(Profile.id == profile_id, Profile.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def create_profile(
    db: AsyncSession,
    user_id: UUID,
    name: str,
    weight_kg: float,
    load_kg: float,
    fitness_level: str,
    surface_type: str,
) -> Profile:
    profile = Profile(
        user_id=user_id,
        name=name,
        weight_kg=weight_kg,
        load_kg=load_kg,
        fitness_level=fitness_level,
        surface_type=surface_type,
    )
    db.add(profile)
    await db.flush()
    await db.refresh(profile)
    return profile


async def update_profile(
    db: AsyncSession,
    user_id: UUID,
    profile_id: UUID,
    **fields,
) -> Profile | None:
    profile = await get_profile(db, user_id, profile_id)
    if not profile:
        return None
    for key, value in fields.items():
        if value is not None:
            setattr(profile, key, value)
    await db.flush()
    await db.refresh(profile)
    return profile


async def delete_profile(db: AsyncSession, user_id: UUID, profile_id: UUID) -> bool:
    profile = await get_profile(db, user_id, profile_id)
    if not profile:
        return False
    await db.delete(profile)
    return True


async def set_default(db: AsyncSession, user_id: UUID, profile_id: UUID) -> Profile | None:
    profile = await get_profile(db, user_id, profile_id)
    if not profile:
        return None

    # Clear all defaults for this user
    result = await db.execute(
        select(Profile).where(Profile.user_id == user_id, Profile.is_default == True)
    )
    for p in result.scalars().all():
        p.is_default = False

    profile.is_default = True
    await db.flush()
    await db.refresh(profile)
    return profile
