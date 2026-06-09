from fastapi import APIRouter

from app.api.v1.endpoints import health, climate
from app.modules.dat.router import dem_router, router as dat_router

api_router = APIRouter()

api_router.include_router(health.router, tags=["System"])
api_router.include_router(dat_router, prefix="/routes", tags=["Routes"])
api_router.include_router(dem_router, prefix="/dem", tags=["DEM"])
api_router.include_router(climate.router, prefix="/climate", tags=["Climate"])
