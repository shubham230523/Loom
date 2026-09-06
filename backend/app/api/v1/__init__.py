from fastapi import APIRouter
from backend.app.api.v1.health import router as health_router
from backend.app.api.v1.auth import auth_router
from backend.app.api.v1.users import router as users_router
from backend.app.api.v1.repositories import router as repositories_router
from backend.app.api.v1.recommendations import router as recommendations_router

api_v1_router = APIRouter()
api_v1_router.include_router(health_router, tags=["health"])
api_v1_router.include_router(auth_router, prefix="/auth")
api_v1_router.include_router(users_router, tags=["users"])
api_v1_router.include_router(repositories_router, prefix="/repositories", tags=["repositories"])
api_v1_router.include_router(recommendations_router, prefix="/recommendations", tags=["recommendations"])
