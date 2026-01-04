"""
AIKU Configuration

Pydantic settings for environment-based configuration.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )

    # App
    APP_NAME: str = "AIKU Travel Agent"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    API_VERSION: str = "v1"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Supabase
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str

    # CORS - Allow localhost for dev, production domain, and wildcard
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001", "https://secoa.ai", "https://www.secoa.ai", "*"]

    # Frontend URL for share links (production default, override with FRONTEND_URL env var for local dev)
    FRONTEND_URL: str = "https://secoa.ai"

    # LLM Configuration
    ANTHROPIC_API_KEY: str
    DEFAULT_LLM_MODEL: str = "claude-sonnet-4-5-20250929"
    LLM_MAX_TOKENS: int = 16384
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_ITERATIONS: int = 50

    # Google Cloud (for FlightsAPI)
    GOOGLE_SERVICE_ACCOUNT_FILE: Optional[str] = "api-key.json"
    FLIGHTS_API_KEY: str = "ff-2026-ilker-secret-xyz123"
    FLIGHTS_API_URL: str = "https://fast-flights-api-1042410626896.europe-west1.run.app"

    # External Travel Agents
    WEATHER_AGENT_URL: str = "https://weather-agent-seven.vercel.app"
    FLIGHT_AGENT_URL: str = "https://flight-agent.vercel.app"
    HOTEL_AGENT_URL: str = "https://hotel-agent-delta.vercel.app"
    TRANSFER_AGENT_URL: str = "https://transfer-agent.vercel.app"
    ACTIVITIES_AGENT_URL: str = "https://activities-agent.vercel.app"
    EXCHANGE_AGENT_URL: str = "https://exchange-agent.vercel.app"
    UTILITY_AGENT_URL: str = "https://utility-agent.vercel.app"

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"


settings = Settings()
