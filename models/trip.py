"""
Trip model
"""
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from .base import BaseModel
import enum


class TripStatus(str, enum.Enum):
    DRAFT = "draft"
    PLANNING = "planning"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"


class Trip(BaseModel):
    __tablename__ = "trips"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    destination = Column(String, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    budget = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    travelers = Column(Integer, default=1)
    preferences = Column(JSONB, nullable=False)
    status = Column(SQLEnum(TripStatus), default=TripStatus.DRAFT)

    # Relationships
    user = relationship("User", back_populates="trips")
    itinerary = relationship("Itinerary", back_populates="trip", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Trip(id={self.id}, destination={self.destination}, status={self.status})>"
