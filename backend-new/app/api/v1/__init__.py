"""
API v1 router
"""
from fastapi import APIRouter

from app.api.v1.endpoints import leaders, auth

router = APIRouter()

# Include endpoint routers
router.include_router(leaders.router, prefix="/leaders", tags=["leaders"])
router.include_router(auth.router, prefix="/auth", tags=["authentication"])
