import enum
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date


class UNITS(str, enum.Enum):
    METRIC = "metric"
    IMPERIAL = "imperial"


class TemperatureData(BaseModel):
    min: float
    max: float
    unit: str
    avg: Optional[float]
    morning: Optional[float]
    afternoon: Optional[float]
    evening: Optional[float]
    night: Optional[float]


class PrecipitationData(BaseModel):
    total: float
    rain: Optional[float]
    snow: Optional[float]


class WeatherForecast(BaseModel):
    date: str
    temperature: TemperatureData
    humidity: float
    wind_speed: float
    precipitation: PrecipitationData
    condition: Optional[str]
    description: Optional[str]
    icon: Optional[str]
    wind_direction: Optional[float]
    cloudiness: Optional[float]
    pressure: Optional[float]