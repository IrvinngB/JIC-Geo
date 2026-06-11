"""Climate endpoints - CLI phase."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.cli import repository as cli_repo
from app.modules.cli.schemas import ClimateCurrentResponse

router = APIRouter()
DB_DEPENDENCY = Depends(get_db)


@router.get("/current", response_model=ClimateCurrentResponse)
async def get_current_climate(
    lat: float,
    lon: float,
    db: AsyncSession = DB_DEPENDENCY,
) -> ClimateCurrentResponse:
    """Return cached or freshly fetched climate data for a location. CLI-01, CLI-07"""
    cached = await cli_repo.get_cached_climate(db, lat, lon)
    if cached is not None:
        return ClimateCurrentResponse(**cached.model_dump(), lat=lat, lon=lon, cached=True)

    try:
        climate = await cli_repo.fetch_open_meteo(lat, lon)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Climate provider unavailable: {exc}",
        ) from exc

    await cli_repo.upsert_climate_zone(db, climate, lat, lon)
    await db.commit()
    return ClimateCurrentResponse(**climate.model_dump(), lat=lat, lon=lon, cached=False)
