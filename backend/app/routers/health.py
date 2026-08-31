"""Health check endpoint."""

from fastapi import APIRouter

from app.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check():
    """Return application health status."""
    settings = get_settings()
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "service": "BhuDrishti 3D Backend",
    }
