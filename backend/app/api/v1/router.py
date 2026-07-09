from fastapi import APIRouter
from backend.app.api.v1.endpoints import health, camera
from backend.app.api.v1 import analytics

api_router = APIRouter()

# Register endpoint sub-routers
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(camera.router, prefix="/camera", tags=["Camera"])
api_router.include_router(analytics.router, tags=["Analytics V1"])

