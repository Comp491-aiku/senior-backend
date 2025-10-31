"""
Weather API endpoints
"""
from fastapi import APIRouter
from typing import List
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()


class WeatherForecast(BaseModel):
    date: datetime
    temperature: dict
    condition: str
    icon: str
    humidity: int
    wind_speed: float
    precipitation: float


@router.get("", response_model=List[WeatherForecast])
async def get_weather_forecast(
    location: str,
    startDate: str,
    endDate: str,
):
    """
    Get weather forecast for a location
    """
    # TODO: Implement weather forecast using OpenWeatherMap API
    return []
