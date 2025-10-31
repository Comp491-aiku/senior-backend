"""
Itinerary models
"""
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from .base import BaseModel


class Itinerary(BaseModel):
    __tablename__ = "itineraries"

    trip_id = Column(UUID(as_uuid=True), ForeignKey("trips.id"), nullable=False, unique=True)
    total_cost = Column(Float, default=0.0)
    generated_at = Column(DateTime, nullable=False)
    days_data = Column(JSONB, nullable=False)  # Store complete day itineraries as JSON

    # Relationships
    trip = relationship("Trip", back_populates="itinerary")
    activities = relationship("Activity", back_populates="itinerary", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Itinerary(id={self.id}, trip_id={self.trip_id})>"


class DayItinerary(BaseModel):
    """
    Individual day within an itinerary
    This can be stored as JSONB in the Itinerary model or as separate records
    """
    __tablename__ = "day_itineraries"

    itinerary_id = Column(UUID(as_uuid=True), ForeignKey("itineraries.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    day_number = Column(Integer, nullable=False)
    activities_data = Column(JSONB)
    meals_data = Column(JSONB)
    accommodation_data = Column(JSONB)
    transportation_data = Column(JSONB)
    weather_data = Column(JSONB)

    def __repr__(self):
        return f"<DayItinerary(id={self.id}, day={self.day_number})>"


class Activity(BaseModel):
    """
    Individual activity within an itinerary
    """
    __tablename__ = "activities"

    itinerary_id = Column(UUID(as_uuid=True), ForeignKey("itineraries.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    start_time = Column(String)
    end_time = Column(String)
    duration = Column(Integer)  # in minutes
    location_data = Column(JSONB)
    cost = Column(Float, default=0.0)
    category = Column(String)
    booking_url = Column(String, nullable=True)
    rating = Column(Float, nullable=True)

    # Relationships
    itinerary = relationship("Itinerary", back_populates="activities")

    def __repr__(self):
        return f"<Activity(id={self.id}, name={self.name})>"
