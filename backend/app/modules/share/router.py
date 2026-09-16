"""Share endpoints — create and view public shared routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.models import User
from app.db.session import get_db
from app.modules.share.schemas import ShareCreate, ShareResponse, SharedRoutePublic
from app.modules.share.service import create_share, get_shared_by_code

router = APIRouter()


@router.post("", response_model=ShareResponse)
async def create_shared_link(
    body: ShareCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    history_id = UUID(body.history_id)
    share = await create_share(db, history_id, current_user.id)
    if not share:
        raise HTTPException(status_code=404, detail="History not found")
    return ShareResponse(
        id=str(share.id),
        share_code=share.share_code,
        url=f"/share/{share.share_code}",
        created_at=share.created_at,
    )


@router.get("/{code}", response_model=SharedRoutePublic)
async def get_shared_route(
    code: str,
    db: AsyncSession = Depends(get_db),
):
    result = await get_shared_by_code(db, code)
    if not result:
        raise HTTPException(status_code=404, detail="Shared route not found")
    share, history = result
    return SharedRoutePublic(
        route_name=history.route_name,
        mide_global=history.mide_global,
        total_distance_km=history.total_distance_km,
        estimated_time_h=history.estimated_time_h,
        total_kcal=history.total_kcal,
        elevation_gain_m=history.elevation_gain_m,
        analysis_json=history.analysis_json,
        created_at=history.created_at,
        view_count=share.view_count,
    )
