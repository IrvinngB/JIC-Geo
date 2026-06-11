from fastapi import APIRouter

from app.api.v1.endpoints import analysis, health, climate
from app.modules.dat.router import dem_router, router as dat_router
from app.modules.grf.router import router as grf_router
from app.modules.rut.router import router as rut_router

api_router = APIRouter()

api_router.include_router(health.router, tags=["System"])
api_router.include_router(dat_router, prefix="/routes", tags=["Routes"])
api_router.include_router(rut_router, prefix="/routes", tags=["Routes"])
api_router.include_router(analysis.router, prefix="/routes", tags=["Analysis"])
api_router.include_router(grf_router, prefix="/routes", tags=["Routing"])
api_router.include_router(dem_router, prefix="/dem", tags=["DEM"])
api_router.include_router(climate.router, prefix="/climate", tags=["Climate"])
