"""
Dependencies file for global deps
"""
from api import OpenWeatherClient


def get_weather_client() -> OpenWeatherClient:
    return OpenWeatherClient()
