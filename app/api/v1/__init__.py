"""
API v1 Router

Combines all v1 API routes.
"""

from fastapi import APIRouter

from app.api.v1.health import router as health_router
from app.api.v1.auth import router as auth_router
from app.api.v1.chat import router as chat_router
from app.api.v1.conversations import router as conversations_router

# Create main v1 router
router = APIRouter(prefix="/v1")

# Include all routers
router.include_router(health_router)
router.include_router(auth_router)
router.include_router(chat_router)
router.include_router(conversations_router)

__all__ = ["router"]
