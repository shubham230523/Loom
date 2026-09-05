from fastapi import APIRouter
from backend.app.config import settings

router = APIRouter()

@router.get("/health")
async def get_health():
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "version": "1.0.0"
    }
