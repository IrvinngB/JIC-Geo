"""Climate endpoint stubs — implemented in Phase 4."""

from fastapi import APIRouter

router = APIRouter()


# API-07
@router.get("/current")
async def get_current_climate(lat: float, lon: float) -> dict:
    """Return cached climate data for a location. Implemented in Phase 4."""
    raise NotImplementedError
