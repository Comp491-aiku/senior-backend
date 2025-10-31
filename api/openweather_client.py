"""
OpenWeatherMap API Client for weather forecasts
"""
import httpx
from typing import List, Dict, Any
from datetime import datetime
from utils.config import settings
import logging

logger = logging.getLogger(__name__)


class OpenWeatherClient:
    """
    Client for OpenWeatherMap API
    Provides weather forecasts and current conditions
    """

    def __init__(self):
        self.api_key = settings.OPENWEATHER_API_KEY
        self.base_url = "https://api.openweathermap.org/data/2.5"

    async def get_forecast(
        self,
        location: str,
        start_date: datetime,
        end_date: datetime,
        units: str = "metric",
    ) -> List[Dict[str, Any]]:
        """
        Get weather forecast for a location

        Args:
            location: City name
            start_date: Start date for forecast
            end_date: End date for forecast
            units: Temperature units (metric, imperial)

        Returns:
            List of daily weather forecasts
        """
        try:
            # First, get coordinates for the location
            coordinates = await self._get_coordinates(location)
            if not coordinates:
                return []

            # Get forecast
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/forecast",
                    params={
                        "lat": coordinates["lat"],
                        "lon": coordinates["lon"],
                        "appid": self.api_key,
                        "units": units,
                    },
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()

                # Process and filter forecast data
                forecasts = self._process_forecast(data, start_date, end_date)
                return forecasts

        except Exception as e:
            logger.error(f"Error getting weather forecast: {str(e)}")
            return []

    async def _get_coordinates(self, location: str) -> Dict[str, float] | None:
        """
        Get coordinates for a location name

        Args:
            location: City name

        Returns:
            Dictionary with lat and lon
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "http://api.openweathermap.org/geo/1.0/direct",
                    params={"q": location, "limit": 1, "appid": self.api_key},
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()

                if data:
                    return {"lat": data[0]["lat"], "lon": data[0]["lon"]}
                return None

        except Exception as e:
            logger.error(f"Error getting coordinates: {str(e)}")
            return None

    def _process_forecast(
        self, data: Dict[str, Any], start_date: datetime, end_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Process raw forecast data into daily summaries

        Args:
            data: Raw API response
            start_date: Filter start date
            end_date: Filter end date

        Returns:
            List of daily forecasts
        """
        # TODO: Implement proper forecast processing
        # Group by day, calculate averages, etc.
        forecasts = []
        for item in data.get("list", []):
            forecast_date = datetime.fromtimestamp(item["dt"])
            if start_date <= forecast_date <= end_date:
                forecasts.append(
                    {
                        "date": forecast_date.isoformat(),
                        "temperature": {
                            "min": item["main"]["temp_min"],
                            "max": item["main"]["temp_max"],
                            "unit": "celsius",
                        },
                        "condition": item["weather"][0]["main"],
                        "description": item["weather"][0]["description"],
                        "icon": item["weather"][0]["icon"],
                        "humidity": item["main"]["humidity"],
                        "wind_speed": item["wind"]["speed"],
                        "precipitation": item.get("rain", {}).get("3h", 0),
                    }
                )
        return forecasts
