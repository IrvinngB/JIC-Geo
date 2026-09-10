"""User profile endpoints — CRUD for hiker profiles (separate from biomechanical PRF router)."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.models import User
from app.db.session import get_db
from app.modules.prf.user_schemas import UserProfileCreate, UserProfileResponse, UserProfileUpdate
from app.modules.prf.user_service import (
    create_profile,
    delete_profile,
    get_profile,
    list_profiles,
    set_default,
    update_profile,
)

router = APIRouter()


@router.get("", response_model=list[UserProfileResponse])
async def get_profiles(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await list_profiles(db, current_user.id)


@router.post("", response_model=UserProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_new_profile(
    body: UserProfileCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.load_kg >= body.weight_kg:
        raise HTTPException(status_code=422, detail="Load must be less than body weight")

    return await create_profile(
        db,
        user_id=current_user.id,
        name=body.name,
        weight_kg=body.weight_kg,
        load_kg=body.load_kg,
        fitness_level=body.fitness_level,
        surface_type=body.surface_type,
    )


@router.get("/{profile_id}", response_model=UserProfileResponse)
async def get_profile_detail(
    profile_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await get_profile(db, current_user.id, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.put("/{profile_id}", response_model=UserProfileResponse)
async def update_profile_detail(
    profile_id: UUID,
    body: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await update_profile(
        db, current_user.id, profile_id, **body.model_dump(exclude_unset=True)
    )
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_profile(
    profile_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    deleted = await delete_profile(db, current_user.id, profile_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Profile not found")


@router.put("/{profile_id}/default", response_model=UserProfileResponse)
async def set_profile_default(
    profile_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await set_default(db, current_user.id, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile
