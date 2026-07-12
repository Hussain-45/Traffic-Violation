from fastapi import APIRouter
from backend.app.api.v1.endpoints import health, camera
from backend.app.api.v1 import admin, auth, analytics, reports
from backend.app.routes import violations, settings, dashboard, video_analysis

api_router = APIRouter()

# Register endpoint sub-routers
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(camera.router, prefix="/camera", tags=["Camera"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin V1"])
api_router.include_router(auth.router, prefix="/auth", tags=["Auth V1"])

# Register application module routers
api_router.include_router(violations.router, tags=["Violations"])
api_router.include_router(settings.router, tags=["Settings"])
api_router.include_router(analytics.router, tags=["Analytics"])
api_router.include_router(reports.router, tags=["Reports"])
api_router.include_router(dashboard.router, tags=["Dashboard"])
api_router.include_router(video_analysis.router, tags=["Video Analysis"])

