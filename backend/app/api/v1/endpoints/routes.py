"""
Routes endpoints — stubs for Phases 1–7.
Each endpoint is implemented when its phase is reached.
"""

from fastapi import APIRouter

router = APIRouter()


# API-02 — Phase 1
@router.post("/upload")
async def upload_route() -> dict:
    """Upload a GPX or GeoJSON route. Implemented in Phase 1."""
    raise NotImplementedError


# API-01 — Phase 7
@router.post("/analyze")
async def analyze_route() -> dict:
    """Analyze a route and return risk index per segment. Implemented in Phase 7."""
    raise NotImplementedError


# API-03 — Phase 7
@router.get("/{route_id}/risk")
async def get_route_risk(route_id: str) -> dict:
    """Get current risk index for a persisted route. Implemented in Phase 7."""
    raise NotImplementedError


# API-04 — Phase 7
@router.post("/{route_id}/simulate")
async def simulate_route(route_id: str) -> dict:
    """Calculate route risk with simulated climate. Implemented in Phase 7."""
    raise NotImplementedError


# API-05 — Phase 7
@router.get("/{route_id}/segments")
async def get_route_segments(route_id: str) -> dict:
    """Get segments with attributes for a persisted route. Implemented in Phase 7."""
    raise NotImplementedError


# API-06 — Phase 7
@router.post("/optimal-path")
async def optimal_path() -> dict:
    """Find least-cost path between two graph nodes. Implemented in Phase 7."""
    raise NotImplementedError
