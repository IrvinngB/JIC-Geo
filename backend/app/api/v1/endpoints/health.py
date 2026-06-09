"""API-08 — Health check endpoint."""

from fastapi import APIRouter
from sqlalchemy import text

from app.db.session import AsyncSessionLocal

router = APIRouter()


@router.get("/health")
async def health_check() -> dict:
    """Health check — verifies PostGIS and pgRouting connectivity."""
    result = {"status": "ok", "postgis": None, "pgrouting": None}

    try:
        async with AsyncSessionLocal() as session:
            postgis = await session.execute(text("SELECT postgis_lib_version()"))
            result["postgis"] = postgis.scalar()

            pgrouting = await session.execute(text("SELECT pgr_version()"))
            result["pgrouting"] = pgrouting.scalar()
    except Exception as exc:
        result["status"] = "degraded"
        result["error"] = str(exc)

    return result
