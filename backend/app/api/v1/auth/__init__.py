from fastapi import APIRouter
from backend.app.api.v1.auth.github import router as github_router
from backend.app.api.v1.auth.me import router as me_router

auth_router = APIRouter()
auth_router.include_router(github_router, tags=["auth"])
auth_router.include_router(me_router, tags=["auth"])
