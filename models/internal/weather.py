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
    avg: Optional[float] = None
    morning: Optional[float] = None
    afternoon: Optional[float] = None
    evening: Optional[float] = None
    night: Optional[float] = None


class PrecipitationData(BaseModel):
    total: float
    rain: Optional[float] = None
    snow: Optional[float] = None


class WeatherForecast(BaseModel):
    date: str
    temperature: TemperatureData
    humidity: float
    wind_speed: float
    precipitation: PrecipitationData
    condition: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    wind_direction: Optional[float] = None
    cloudiness: Optional[float] = None
    pressure: Optional[float] = None