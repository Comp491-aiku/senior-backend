"""
Health Check Endpoints

Application health and status endpoints.
"""

from fastapi import APIRouter

from app.config import settings
from app.api.schemas import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.

    Returns application status, version, and environment.
    Used by load balancers and monitoring systems.
    """
    return HealthResponse(
        status="healthy",
        version=settings.API_VERSION,
        environment=settings.APP_ENV,
    )


@router.get("/")
async def root():
    """Root endpoint - redirects to health check."""
    return {
        "name": settings.APP_NAME,
        "version": settings.API_VERSION,
        "status": "running",
        "docs": "/docs",
    }
