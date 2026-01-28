from __future__ import annotations

from functools import lru_cache
from typing import Literal, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="TRIP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: Literal["dev", "prod", "test"] = "dev"
    app_name: str = "agentic-trip-planner"

    database_url: str = "sqlite+aiosqlite:///./trip_planner.db"
    redis_url: Optional[str] = None

    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-1.5-flash"

    openweather_api_key: Optional[str] = None
    google_places_api_key: Optional[str] = None
    distance_matrix_api_key: Optional[str] = None
    currency_api_key: Optional[str] = None

    cache_ttl_weather_seconds: int = 60 * 60
    cache_ttl_places_seconds: int = 60 * 60 * 24
    cache_ttl_travel_seconds: int = 60 * 60
    cache_ttl_currency_seconds: int = 60 * 60 * 12

    planner_buffer_minutes: int = 20


@lru_cache
def get_settings() -> Settings:
    return Settings()
