from fastapi import APIRouter

from app.api.v1.endpoints import health, routes, climate

api_router = APIRouter()

api_router.include_router(health.router, tags=["System"])
api_router.include_router(routes.router, prefix="/routes", tags=["Routes"])
api_router.include_router(climate.router, prefix="/climate", tags=["Climate"])
