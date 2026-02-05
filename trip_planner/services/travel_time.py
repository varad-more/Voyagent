"""
Travel time calculation service.
"""
import logging
import requests
from django.conf import settings
from trip_planner.core.cache import cache_client

logger = logging.getLogger(__name__)
DEFAULT_TRAVEL_TIME = 20


def _parse_coords(value: str):
    """Parse lat,lon from string."""
    if "," not in value:
        return None
    try:
        parts = value.split(",", 1)
        return float(parts[0].strip()), float(parts[1].strip())
    except ValueError:
        return None


def get_travel_time_minutes(origin: str, destination: str) -> dict:
    """Calculate travel time between locations."""
    cached = cache_client.get_travel_time(origin, destination)
    if cached is not None:
        return {"travel_time_minutes": cached}
    
    # Try Google Distance Matrix
    api_key = settings.DISTANCE_MATRIX_API_KEY
    if api_key:
        try:
            resp = requests.get(
                "https://maps.googleapis.com/maps/api/distancematrix/json",
                params={"origins": origin, "destinations": destination, "key": api_key, "units": "metric"},
                timeout=15
            )
            resp.raise_for_status()
            data = resp.json()
            rows = data.get("rows", [])
            if rows and rows[0].get("elements"):
                element = rows[0]["elements"][0]
                if element.get("status") == "OK":
                    minutes = int(element["duration"]["value"] / 60)
                    cache_client.set_travel_time(origin, destination, minutes)
                    return {"travel_time_minutes": minutes}
        except Exception as e:
            logger.warning(f"Distance Matrix failed: {e}")
    
    # Try OSRM with coordinates
    origin_coords = _parse_coords(origin)
    dest_coords = _parse_coords(destination)
    
    if origin_coords and dest_coords:
        try:
            url = f"https://router.project-osrm.org/route/v1/driving/{origin_coords[1]},{origin_coords[0]};{dest_coords[1]},{dest_coords[0]}"
            resp = requests.get(url, params={"overview": "false"}, timeout=10)
            resp.raise_for_status()
            routes = resp.json().get("routes", [])
            if routes:
                minutes = int(routes[0]["duration"] / 60)
                cache_client.set_travel_time(origin, destination, minutes)
                return {"travel_time_minutes": minutes}
        except Exception as e:
            logger.warning(f"OSRM failed: {e}")
    
    # Fallback
    cache_client.set_travel_time(origin, destination, DEFAULT_TRAVEL_TIME)
    return {"travel_time_minutes": DEFAULT_TRAVEL_TIME}
