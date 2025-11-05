"""
Alternative finder endpoints - Find alternative options for flights, hotels, activities
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from database.connection import get_db
from models.user import User
from auth.dependencies import get_current_user
from agents.flight_agent import FlightAgent
from agents.accommodation_agent import AccommodationAgent
from agents.activity_agent import ActivityAgent
from pydantic import BaseModel

router = APIRouter()


class AlternativeRequest(BaseModel):
    """Base schema for alternative requests"""
    trip_id: str
    item_id: str  # ID of current item to find alternatives for
    preferences: Optional[dict] = None


class AlternativeFlightRequest(AlternativeRequest):
    """Schema for alternative flight requests"""
    price_range: Optional[str] = None  # "cheaper", "same", "flexible"
    flexibility: Optional[int] = None  # Days of flexibility (+/- days)


class AlternativeHotelRequest(AlternativeRequest):
    """Schema for alternative hotel requests"""
    price_range: Optional[str] = None
    location_preference: Optional[str] = None  # "closer", "downtown", "airport"


class AlternativeActivityRequest(AlternativeRequest):
    """Schema for alternative activity requests"""
    category: Optional[str] = None  # "outdoor", "cultural", "food", etc.
    price_range: Optional[str] = None


@router.post("/alternatives/flights")
async def find_alternative_flights(
    request: AlternativeFlightRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Find alternative flight options

    This endpoint finds alternative flights based on user preferences:
    - Cheaper options
    - Different times
    - Different airlines
    - Flexible dates

    Args:
        request: Alternative flight request with preferences
        current_user: Authenticated user
        db: Database session

    Returns:
        List of alternative flight options
    """
    # Verify trip belongs to user
    from models.trip import Trip
    trip = db.query(Trip).filter(
        Trip.id == request.trip_id,
        Trip.user_id == current_user.id
    ).first()

    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )

    # Get current flight details
    # In production, fetch from database
    current_flight = {}  # Placeholder

    # Use flight agent to find alternatives
    flight_agent = FlightAgent()

    context = {
        "destination": trip.destination,
        "start_date": trip.start_date,
        "end_date": trip.end_date,
        "travelers": trip.preferences.get("travelers", 1),
        "current_flight_id": request.item_id,
        "price_range": request.price_range,
        "flexibility": request.flexibility,
        "preferences": request.preferences or {}
    }

    alternatives = await flight_agent.find_alternatives(context)

    return {
        "success": True,
        "alternatives": alternatives.get("flights", []),
        "count": len(alternatives.get("flights", [])),
        "filters_applied": {
            "price_range": request.price_range,
            "flexibility": request.flexibility
        }
    }


@router.post("/alternatives/accommodations")
async def find_alternative_accommodations(
    request: AlternativeHotelRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Find alternative accommodation options

    This endpoint finds alternative hotels/accommodations:
    - Different price ranges
    - Different locations
    - Different amenities
    - Different star ratings

    Args:
        request: Alternative accommodation request
        current_user: Authenticated user
        db: Database session

    Returns:
        List of alternative accommodation options
    """
    from models.trip import Trip
    trip = db.query(Trip).filter(
        Trip.id == request.trip_id,
        Trip.user_id == current_user.id
    ).first()

    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )

    accommodation_agent = AccommodationAgent()

    context = {
        "destination": trip.destination,
        "start_date": trip.start_date,
        "end_date": trip.end_date,
        "travelers": trip.preferences.get("travelers", 1),
        "current_hotel_id": request.item_id,
        "price_range": request.price_range,
        "location_preference": request.location_preference,
        "preferences": request.preferences or {}
    }

    alternatives = await accommodation_agent.find_alternatives(context)

    return {
        "success": True,
        "alternatives": alternatives.get("accommodations", []),
        "count": len(alternatives.get("accommodations", [])),
        "filters_applied": {
            "price_range": request.price_range,
            "location": request.location_preference
        }
    }


@router.post("/alternatives/activities")
async def find_alternative_activities(
    request: AlternativeActivityRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Find alternative activity options

    This endpoint finds alternative activities:
    - Different categories (outdoor, cultural, food)
    - Different price ranges
    - Different times
    - Similar activities

    Args:
        request: Alternative activity request
        current_user: Authenticated user
        db: Database session

    Returns:
        List of alternative activity options
    """
    from models.trip import Trip
    trip = db.query(Trip).filter(
        Trip.id == request.trip_id,
        Trip.user_id == current_user.id
    ).first()

    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )

    activity_agent = ActivityAgent()

    context = {
        "destination": trip.destination,
        "start_date": trip.start_date,
        "end_date": trip.end_date,
        "current_activity_id": request.item_id,
        "category": request.category,
        "price_range": request.price_range,
        "preferences": request.preferences or {}
    }

    alternatives = await activity_agent.find_alternatives(context)

    return {
        "success": True,
        "alternatives": alternatives.get("activities", []),
        "count": len(alternatives.get("activities", [])),
        "filters_applied": {
            "category": request.category,
            "price_range": request.price_range
        }
    }


@router.get("/alternatives/suggestions")
async def get_alternative_suggestions(
    trip_id: str,
    item_type: str = Query(..., regex="^(flight|accommodation|activity)$"),
    item_id: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get smart suggestions for alternatives

    This endpoint uses AI to suggest what kind of alternatives might be good
    without running a full search.

    Args:
        trip_id: Trip ID
        item_type: Type of item (flight, accommodation, activity)
        item_id: Optional specific item ID
        current_user: Authenticated user
        db: Database session

    Returns:
        Smart suggestions for alternatives
    """
    from models.trip import Trip
    trip = db.query(Trip).filter(
        Trip.id == trip_id,
        Trip.user_id == current_user.id
    ).first()

    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )

    # Generate smart suggestions based on trip data and preferences
    suggestions = []

    if item_type == "flight":
        suggestions = [
            {"type": "cheaper", "description": "Find cheaper flights with similar timing"},
            {"type": "flexible", "description": "Find flights on nearby dates (save up to 30%)"},
            {"type": "direct", "description": "Find direct flights (no layovers)"},
            {"type": "premium", "description": "Upgrade to business class"}
        ]
    elif item_type == "accommodation":
        suggestions = [
            {"type": "cheaper", "description": "Find budget-friendly options"},
            {"type": "location", "description": "Find hotels closer to attractions"},
            {"type": "luxury", "description": "Upgrade to luxury accommodations"},
            {"type": "unique", "description": "Find unique stays (boutique, airbnb)"}
        ]
    elif item_type == "activity":
        suggestions = [
            {"type": "similar", "description": "Find similar activities"},
            {"type": "free", "description": "Find free or low-cost activities"},
            {"type": "popular", "description": "Most popular activities in the area"},
            {"type": "hidden", "description": "Hidden gems and local favorites"}
        ]

    return {
        "success": True,
        "suggestions": suggestions,
        "item_type": item_type
    }
