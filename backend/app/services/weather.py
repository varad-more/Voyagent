from __future__ import annotations

import datetime as dt
from collections import defaultdict
from typing import Any

import httpx
import structlog

from app.core.cache import CacheClient
from app.core.config import get_settings


logger = structlog.get_logger(__name__)


async def _stub_weather(start_date: dt.date, end_date: dt.date) -> dict[str, Any]:
    days = []
    current = start_date
    while current <= end_date:
        days.append(
            {
                "date": current.isoformat(),
                "high_c": 24.0,
                "low_c": 15.0,
                "precipitation_chance": 0.2,
                "summary": "Mild with light clouds",
            }
        )
        current += dt.timedelta(days=1)
    return {
        "forecast_source": "stub",
        "overview": "Forecast unavailable; using seasonal averages.",
        "risks": ["Forecast data unavailable; plan flexible indoor options."],
        "daily": days,
    }


async def get_weather(
    *,
    destination: str,
    start_date: dt.date,
    end_date: dt.date,
    session,
) -> dict[str, Any]:
    settings = get_settings()
    cache = CacheClient()
    cache_key = f"weather:{destination}:{start_date}:{end_date}"
    cached = await cache.get(cache_key, session)
    if cached:
        return cached

    if not settings.openweather_api_key:
        payload = await _stub_weather(start_date, end_date)
        await cache.set(
            cache_key, "openweather", payload, settings.cache_ttl_weather_seconds, session
        )
        return payload

    async with httpx.AsyncClient(timeout=15) as client:
        try:
            geo_resp = await client.get(
                "https://api.openweathermap.org/geo/1.0/direct",
                params={"q": destination, "limit": 1, "appid": settings.openweather_api_key},
            )
            geo_resp.raise_for_status()
            geo_data = geo_resp.json()
            if not geo_data:
                logger.warning("openweather_geo_not_found", destination=destination)
                payload = await _stub_weather(start_date, end_date)
                await cache.set(
                    cache_key, "openweather", payload, settings.cache_ttl_weather_seconds, session
                )
                return payload
            lat = geo_data[0]["lat"]
            lon = geo_data[0]["lon"]

            forecast_resp = await client.get(
                "https://api.openweathermap.org/data/2.5/forecast",
                params={"lat": lat, "lon": lon, "appid": settings.openweather_api_key, "units": "metric"},
            )
            forecast_resp.raise_for_status()
            forecast = forecast_resp.json()
        except Exception as exc:
            logger.error("openweather_api_failed", error=str(exc))
            payload = await _stub_weather(start_date, end_date)
            await cache.set(
                cache_key, "openweather", payload, settings.cache_ttl_weather_seconds, session
            )
            return payload

    buckets: dict[dt.date, list[dict[str, Any]]] = defaultdict(list)
    for item in forecast.get("list", []):
        timestamp = dt.datetime.fromtimestamp(item["dt"], tz=dt.timezone.utc).date()
        buckets[timestamp].append(item)

    days = []
    current = start_date
    while current <= end_date:
        entries = buckets.get(current, [])
        if not entries:
            days.append(
                {
                    "date": current.isoformat(),
                    "high_c": 23.0,
                    "low_c": 14.0,
                    "precipitation_chance": 0.2,
                    "summary": "Seasonal average (limited forecast range)",
                }
            )
            current += dt.timedelta(days=1)
            continue
        temps = [entry["main"]["temp"] for entry in entries]
        pops = [entry.get("pop", 0) for entry in entries]
        summary = entries[0]["weather"][0]["description"].title()
        days.append(
            {
                "date": current.isoformat(),
                "high_c": max(temps),
                "low_c": min(temps),
                "precipitation_chance": max(pops) if pops else 0,
                "summary": summary,
            }
        )
        current += dt.timedelta(days=1)

    payload = {
        "forecast_source": "openweather",
        "overview": "Daily forecast based on OpenWeather 5-day model.",
        "risks": [
            "Forecast beyond 5 days is extrapolated; keep an indoor backup.",
        ]
        if (end_date - start_date).days >= 5
        else [],
        "daily": days,
    }
    await cache.set(
        cache_key, "openweather", payload, settings.cache_ttl_weather_seconds, session
    )
    return payload
