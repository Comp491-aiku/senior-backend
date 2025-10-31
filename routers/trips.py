"""
Trip API endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from uuid import UUID

router = APIRouter()


# Pydantic schemas
class TripPreferences(BaseModel):
    accommodation: str
    activities: List[str] = []
    pace: str
    interests: List[str] = []
    dietary_restrictions: Optional[List[str]] = None
    accessibility: Optional[List[str]] = None


class TripCreate(BaseModel):
    destination: str
    start_date: datetime
    end_date: datetime
    budget: float
    currency: str = "USD"
    travelers: int = 1
    preferences: TripPreferences


class TripUpdate(BaseModel):
    destination: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    budget: Optional[float] = None
    currency: Optional[str] = None
    travelers: Optional[int] = None
    preferences: Optional[TripPreferences] = None
    status: Optional[str] = None


class TripResponse(BaseModel):
    id: UUID
    user_id: UUID
    destination: str
    start_date: datetime
    end_date: datetime
    budget: float
    currency: str
    travelers: int
    preferences: dict
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaginatedTripsResponse(BaseModel):
    items: List[TripResponse]
    total: int
    page: int
    pageSize: int
    hasNext: bool
    hasPrev: bool


@router.get("", response_model=PaginatedTripsResponse)
async def get_trips(
    page: int = 1,
    pageSize: int = 10,
    status: Optional[str] = None,
):
    """
    Get all trips with pagination
    """
    # TODO: Implement actual database query
    return PaginatedTripsResponse(
        items=[],
        total=0,
        page=page,
        pageSize=pageSize,
        hasNext=False,
        hasPrev=False,
    )


@router.get("/{trip_id}", response_model=TripResponse)
async def get_trip(trip_id: UUID):
    """
    Get a specific trip by ID
    """
    # TODO: Implement actual database query
    raise HTTPException(status_code=404, detail="Trip not found")


@router.post("", response_model=TripResponse, status_code=201)
async def create_trip(trip: TripCreate):
    """
    Create a new trip
    """
    # TODO: Implement actual database creation
    raise HTTPException(status_code=501, detail="Not implemented")


@router.put("/{trip_id}", response_model=TripResponse)
async def update_trip(trip_id: UUID, trip: TripUpdate):
    """
    Update an existing trip
    """
    # TODO: Implement actual database update
    raise HTTPException(status_code=404, detail="Trip not found")


@router.delete("/{trip_id}", status_code=204)
async def delete_trip(trip_id: UUID):
    """
    Delete a trip
    """
    # TODO: Implement actual database deletion
    raise HTTPException(status_code=404, detail="Trip not found")
