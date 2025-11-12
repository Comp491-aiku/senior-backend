"""
OpenWeatherMap API Client for weather forecasts
"""
import httpx
from typing import List, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict
from utils.config import settings
from models.internal.weather import WeatherForecast, TemperatureData, PrecipitationData
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
        self.onecall_url = "https://api.openweathermap.org/data/3.0/onecall"

    async def get_forecast(
            self,
            location: str,
            start_date: datetime,
            end_date: datetime,
            units: str = "metric",
    ) -> List[WeatherForecast]:
        """
        Get weather forecast for a location

        Strategy:
        - For trips starting <5 days from now: Use free forecast5 API (3-hour intervals)
        - For trips starting ≥5 days from now: Use day_summary API (daily aggregates)

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

            now = datetime.now()
            days_until_trip = (start_date.replace(tzinfo=None) - now).days

            if days_until_trip < 5:
                return await self._get_forecast5(coordinates, start_date, end_date, units)
            else:
                return await self._get_day_summary(coordinates, start_date, end_date, units)

        except Exception as e:
            logger.error(f"Error getting weather forecast: {str(e)}")
            return []

    async def _get_forecast5(
            self,
            coordinates: Dict[str, float],
            start_date: datetime,
            end_date: datetime,
            units: str = "metric",
    ) -> List[WeatherForecast]:

        try:
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

                forecasts = self._process_forecast(data, start_date, end_date, units)
                return forecasts

        except Exception as e:
            logger.error(f"Error getting forecast5 data: {str(e)}")
            return []

    async def _get_day_summary(
            self,
            coordinates: Dict[str, float],
            start_date: datetime,
            end_date: datetime,
            units: str = "metric",
    ) -> List[WeatherForecast]:

        forecasts = []
        current_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = end_date.replace(hour=0, minute=0, second=0, microsecond=0)

        try:
            async with httpx.AsyncClient() as client:
                while current_date <= end:
                    date_str = current_date.strftime("%Y-%m-%d")

                    response = await client.get(
                        f"{self.onecall_url}/day_summary",
                        params={
                            "lat": coordinates["lat"],
                            "lon": coordinates["lon"],
                            "date": date_str,
                            "appid": self.api_key,
                            "units": units,
                        },
                        timeout=30.0,
                    )
                    response.raise_for_status()
                    data = response.json()

                    forecast = self._process_day_summary(data, current_date, units)
                    if forecast:
                        forecasts.append(forecast)

                    current_date += timedelta(days=1)

                return forecasts

        except Exception as e:
            logger.error(f"Error getting day_summary data: {str(e)}")
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
            self,
            data: Dict[str, Any],
            start_date: datetime,
            end_date: datetime,
            units: str = "metric"
    ) -> List[WeatherForecast]:
        """
        Process raw forecast5 data (3-hour intervals) into daily summaries

        Args:
            data: Raw API response from forecast5
            start_date: Filter start date
            end_date: Filter end date
            units: Temperature units (metric, imperial)

        Returns:
            List of WeatherForecast objects (one per day)
        """
        try:
            daily_data = defaultdict(list)

            for item in data.get("list", []):
                forecast_date = datetime.fromtimestamp(item["dt"])

                if start_date.replace(tzinfo=None) <= forecast_date <= end_date.replace(tzinfo=None):
                    date_key = forecast_date.date()
                    daily_data[date_key].append(item)

            forecasts = []
            for date_key in sorted(daily_data.keys()):
                day_items = daily_data[date_key]

                temps = [item["main"]["temp"] for item in day_items]
                temp_mins = [item["main"]["temp_min"] for item in day_items]
                temp_maxs = [item["main"]["temp_max"] for item in day_items]
                humidities = [item["main"]["humidity"] for item in day_items]
                wind_speeds = [item["wind"]["speed"] for item in day_items]
                conditions = [item["weather"][0]["main"] for item in day_items]
                descriptions = [item["weather"][0]["description"] for item in day_items]

                total_rain = sum(item.get("rain", {}).get("3h", 0) for item in day_items)
                total_snow = sum(item.get("snow", {}).get("3h", 0) for item in day_items)

                most_common_condition = max(set(conditions), key=conditions.count)
                condition_description = descriptions[conditions.index(most_common_condition)]
                condition_icon = day_items[conditions.index(most_common_condition)]["weather"][0]["icon"]
                cloudiness = sum(item["clouds"]["all"] for item in day_items) / len(day_items)

                forecast = WeatherForecast(
                    date=date_key.isoformat(),
                    temperature=TemperatureData(
                        min=min(temp_mins),
                        max=max(temp_maxs),
                        unit="celsius" if units == "metric" else "fahrenheit",
                        avg=sum(temps) / len(temps),
                    ),
                    humidity=sum(humidities) / len(humidities),
                    wind_speed=sum(wind_speeds) / len(wind_speeds),
                    precipitation=PrecipitationData(
                        total=round(total_rain + total_snow, 2),
                        rain=round(total_rain, 2) if total_rain > 0 else None,
                        snow=round(total_snow, 2) if total_snow > 0 else None,
                    ),
                    condition=most_common_condition,
                    description=condition_description,
                    icon=condition_icon,
                    cloudiness=round(cloudiness),
                )
                forecasts.append(forecast)

            return forecasts
        except Exception as e:
            logger.error(f"Error processing forecast data: {str(e)}")
            return []

    def _process_day_summary(
            self,
            data: Dict[str, Any],
            date: datetime,
            units: str = "metric"
    ) -> WeatherForecast | None:
        """
        Process day_summary API response into WeatherForecast object

        Args:
            data: Raw API response from day_summary
            date: Date for this forecast
            units: Temperature units (metric, imperial)

        Returns:
            WeatherForecast object or None if error
        """
        try:
            temp_data = data.get("temperature", {})
            precipitation_data = data.get("precipitation", {})
            wind_data = data.get("wind", {})
            cloud_data = data.get("cloud_cover", {})
            humidity_data = data.get("humidity", {})

            return WeatherForecast(
                date=date.date().isoformat(),
                temperature=TemperatureData(
                    min=temp_data.get("min"),
                    max=temp_data.get("max"),
                    unit="celsius" if units == "metric" else "fahrenheit",
                    avg=(temp_data.get("min", 0) + temp_data.get("max", 0)) / 2,
                    morning=temp_data.get("morning"),
                    afternoon=temp_data.get("afternoon"),
                    evening=temp_data.get("evening"),
                    night=temp_data.get("night"),
                ),
                humidity=humidity_data.get("afternoon", 0),
                wind_speed=wind_data.get("max", {}).get("speed", 0),
                precipitation=PrecipitationData(
                    total=precipitation_data.get("total", 0),
                    rain=precipitation_data.get("total", 0) if precipitation_data.get("total", 0) > 0 else None,
                    snow=None,
                ),
                condition="Clear",  # day_summary doesn't provide condition text
                description=f"Temperature between {temp_data.get('min')}° and {temp_data.get('max')}°",
                icon="01d",  # Default icon, day_summary doesn't provide this
                wind_direction=wind_data.get("max", {}).get("direction"),
                cloudiness=cloud_data.get("afternoon"),
                pressure=data.get("pressure", {}).get("afternoon"),
            )
        except Exception as e:
            logger.error(f"Error processing day_summary data: {str(e)}")
            return None
