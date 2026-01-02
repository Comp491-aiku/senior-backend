"""
AIKU Backend - Main FastAPI Application
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from routers import trips, itinerary, flights, accommodations, weather, auth, chat, sse, alternatives, collaboration
from utils.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(name)s - %(message)s"
)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered travel planning backend",
    version=settings.API_VERSION,
    debug=settings.DEBUG,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "message": "Welcome to AIKU API",
        "version": settings.API_VERSION,
        "status": "running",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(sse.router, prefix="/api", tags=["sse"])
app.include_router(alternatives.router, prefix="/api", tags=["alternatives"])
app.include_router(collaboration.router, prefix="/api", tags=["collaboration"])
app.include_router(trips.router, prefix="/api/trips", tags=["trips"])
app.include_router(itinerary.router, prefix="/api/trips", tags=["itinerary"])
app.include_router(flights.router, prefix="/api/flights", tags=["flights"])
app.include_router(accommodations.router, prefix="/api/accommodations", tags=["accommodations"])
app.include_router(weather.router, prefix="/api/weather", tags=["weather"])


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": str(exc),
            "message": "An internal server error occurred",
        },
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
