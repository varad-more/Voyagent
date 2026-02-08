"""
OpenWeather API service.
"""
import logging
from datetime import date, timedelta, datetime, timezone
from collections import defaultdict
import requests
from django.conf import settings
from trip_planner.core.cache import cache_client

logger = logging.getLogger(__name__)


def _stub_weather(start_date: date, end_date: date) -> dict:
    """Stub weather data."""
    days = []
    current = start_date
    while current <= end_date:
        days.append({
            "date": current.isoformat(),
            "high_c": 24.0,
            "low_c": 15.0,
            "precipitation_chance": 0.2,
            "summary": "Mild with light clouds",
        })
        current += timedelta(days=1)
    
    return {
        "forecast_source": "stub",
        "overview": "Forecast unavailable; using seasonal averages.",
        "risks": ["Plan flexible indoor options."],
        "daily": days,
    }


def get_weather(destination: str, start_date: date, end_date: date) -> dict:
    """Fetch weather forecast from OpenWeather API."""
    cache_key = f"{start_date}:{end_date}"
    
    cached = cache_client.get_weather(destination, cache_key)
    if cached:
        return cached
    
    api_key = settings.OPENWEATHER_API_KEY
    if not api_key:
        payload = _stub_weather(start_date, end_date)
        cache_client.set_weather(destination, cache_key, payload)
        return payload
    
    try:
        # Geocode
        geo_resp = requests.get(
            "https://api.openweathermap.org/geo/1.0/direct",
            params={"q": destination, "limit": 1, "appid": api_key},
            timeout=15
        )
        geo_resp.raise_for_status()
        geo_data = geo_resp.json()
        
        if not geo_data:
            payload = _stub_weather(start_date, end_date)
            cache_client.set_weather(destination, cache_key, payload)
            return payload
        
        lat, lon = geo_data[0]["lat"], geo_data[0]["lon"]
        
        # Forecast
        forecast_resp = requests.get(
            "https://api.openweathermap.org/data/2.5/forecast",
            params={"lat": lat, "lon": lon, "appid": api_key, "units": "metric"},
            timeout=15
        )
        forecast_resp.raise_for_status()
        forecast = forecast_resp.json()
        
    except Exception as e:
        logger.error(f"Weather API failed: {e}")
        payload = _stub_weather(start_date, end_date)
        cache_client.set_weather(destination, cache_key, payload)
        return payload
    
    # Aggregate by day
    buckets = defaultdict(list)
    for item in forecast.get("list", []):
        ts = datetime.fromtimestamp(item["dt"], tz=timezone.utc).date()
        buckets[ts].append(item)
    
    days = []
    current = start_date
    while current <= end_date:
        entries = buckets.get(current, [])
        if not entries:
            days.append({
                "date": current.isoformat(),
                "high_c": 23.0, "low_c": 14.0,
                "precipitation_chance": 0.2,
                "summary": "Seasonal average",
            })
        else:
            temps = [e["main"]["temp"] for e in entries]
            pops = [e.get("pop", 0) for e in entries]
            days.append({
                "date": current.isoformat(),
                "high_c": max(temps), "low_c": min(temps),
                "precipitation_chance": max(pops) if pops else 0,
                "summary": entries[0]["weather"][0]["description"].title(),
            })
        current += timedelta(days=1)
    
    trip_len = (end_date - start_date).days
    payload = {
        "forecast_source": "openweather",
        "overview": "Based on OpenWeather 5-day forecast.",
        "risks": ["Forecast beyond 5 days is extrapolated."] if trip_len >= 5 else [],
        "daily": days,
    }
    
    cache_client.set_weather(destination, cache_key, payload)
    return payload
