"""
Weather Agent - Handles weather forecast retrieval
"""
from typing import Any, Dict
from .base_agent import BaseAgent
from api.openweather_client import OpenWeatherClient


class WeatherAgent(BaseAgent):
    """
    Agent responsible for fetching weather forecasts
    """

    def __init__(self):
        super().__init__("WeatherAgent")
        self.weather_client = OpenWeatherClient()

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get weather forecast for the trip

        Args:
            context: Dictionary containing:
                - destination: str
                - start_date: datetime
                - end_date: datetime

        Returns:
            Dictionary with daily weather forecasts
        """
        self.log_info(f"Fetching weather for {context.get('destination')}")

        try:
            forecast = await self.weather_client.get_forecast(
                location=context["destination"],
                start_date=context["start_date"],
                end_date=context["end_date"],
            )

            return {
                "daily_forecast": forecast,
                "summary": self._generate_weather_summary(forecast),
            }

        except Exception as e:
            self.log_error(f"Error fetching weather: {str(e)}")
            return {"daily_forecast": [], "summary": "Weather data unavailable"}

    def _generate_weather_summary(self, forecast: list) -> str:
        """Generate a human-readable weather summary"""
        # TODO: Implement weather summary generation
        return "Weather conditions are favorable for travel"
