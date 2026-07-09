from fastapi import APIRouter
from backend.app.core.config import settings

router = APIRouter()

@router.get("/health")
def check_health():
    """
    Standard health check endpoint.
    """
    return {
        "status": "ok",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION
    }
