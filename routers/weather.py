"""
Weather API endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from datetime import datetime

from dependencies import get_weather_client
from utils.validators import validate_date_range
from models.internal.weather import WeatherForecast, UNITS
from api.openweather_client import OpenWeatherClient
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=List[WeatherForecast])
async def get_weather_forecast(
        location: str,
        startDate: str,
        endDate: str,
        units: UNITS = UNITS.METRIC,
        weather_client: OpenWeatherClient = Depends(get_weather_client),
):
    """
    Get weather forecast for a location

    Returns daily weather forecasts for the specified date range.

    Strategy:
    - For trips starting <5 days from now: Uses forecast5 API (free, 3-hour intervals aggregated daily)
    - For trips starting ≥5 days from now: Uses day_summary API (One Call API 3.0)

    Args:
        location: city name
        startDate: start date in ISO format
        endDate: rnd date in ISO format
        units: temperature units - "metric" (Celsius) or "imperial" (Fahrenheit)
        weather_client: depends on weather client

    Returns:
        List of daily weather forecasts
    """
    try:
        start_dt = datetime.fromisoformat(startDate)
        end_dt = datetime.fromisoformat(endDate)

        if not validate_date_range(start_dt, end_dt):
            raise HTTPException(
                status_code=400,
                detail="Start date must be before or equal to end date"
            )

        forecasts = await weather_client.get_forecast(
            location=location,
            start_date=start_dt,
            end_date=end_dt,
            units=units
        )

        if not forecasts:
            raise HTTPException(
                status_code=404,
                detail=f"Could not retrieve weather forecast for location: {location}"
            )

        return forecasts

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Error fetching weather forecast: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve weather forecast. Please try again later."
        )
