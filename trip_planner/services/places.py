"""
Google Places API service.
"""
import logging
import requests
from django.conf import settings
from trip_planner.core.cache import cache_client

logger = logging.getLogger(__name__)


def _stub_attractions(destination: str) -> dict:
    """Stub data when API unavailable."""
    return {
        "attractions": [
            {"name": f"{destination} Old Town", "reason": "Historic district", 
             "score": 0.86, "distance_km": 1.8, "categories": ["historic"], "address": None},
            {"name": f"{destination} Park", "reason": "Scenic area", 
             "score": 0.78, "distance_km": 2.5, "categories": ["nature"], "address": None},
            {"name": f"{destination} Museum", "reason": "Indoor option", 
             "score": 0.73, "distance_km": 3.1, "categories": ["museum"], "address": None},
        ]
    }


def _stub_hotels(destination: str, comfort: str) -> dict:
    """Stub hotel data."""
    return {
        "hotels": [
            {"name": f"{destination} Grand ({comfort})", "rating": 4.5, 
             "address": "Downtown", "price_level": comfort},
            {"name": f"{destination} Inn ({comfort})", "rating": 4.0, 
             "address": "City Center", "price_level": comfort},
        ]
    }


def get_attractions(destination: str, interests: list = None) -> dict:
    """Fetch attractions from Google Places API."""
    interests = interests or []
    interest_key = "-".join(sorted(interests)) if interests else "general"
    
    cached = cache_client.get_places(destination, interest_key)
    if cached:
        return cached
    
    api_key = settings.GOOGLE_PLACES_API_KEY
    if not api_key:
        payload = _stub_attractions(destination)
        cache_client.set_places(destination, interest_key, payload, ttl=settings.CACHE_TTL_ERROR)
        return payload
    
    query = f"top attractions in {destination}"
    if interests:
        query = f"{', '.join(interests)} in {destination}"
    
    try:
        resp = requests.get(
            "https://maps.googleapis.com/maps/api/place/textsearch/json",
            params={"query": query, "key": api_key},
            timeout=20
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.error(f"Places API failed: {e}")
        payload = _stub_attractions(destination)
        cache_client.set_places(destination, interest_key, payload, ttl=settings.CACHE_TTL_ERROR)
        return payload
    
    attractions = []
    for item in data.get("results", [])[:12]:
        rating = item.get("rating", 3.5)
        # Safe access to types
        types_list = item.get("types") or ["attraction"]
        
        attractions.append({
            "name": item.get("name"),
            "reason": types_list[0].replace("_", " ").title(),
            "score": min(1.0, max(0.1, rating / 5)),
            "distance_km": 2.0,
            "categories": item.get("types", []),
            "address": item.get("formatted_address"),
        })
    
    payload = {"attractions": attractions}
    cache_client.set_places(destination, interest_key, payload)
    return payload


def get_hotels(destination: str, comfort_level: str = "midrange") -> dict:
    """Fetch hotels from Google Places API."""
    cache_key = f"hotels:{comfort_level}"
    
    cached = cache_client.get_places(destination, cache_key)
    if cached:
        return cached
    
    api_key = settings.GOOGLE_PLACES_API_KEY
    if not api_key:
        return _stub_hotels(destination, comfort_level)
    
    keywords = {"luxury": "5 star hotel luxury", "budget": "cheap hotel hostel", "midrange": "3 star hotel"}
    query = f"{keywords.get(comfort_level, 'hotel')} in {destination}"
    
    try:
        resp = requests.get(
            "https://maps.googleapis.com/maps/api/place/textsearch/json",
            params={"query": query, "key": api_key},
            timeout=20
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.error(f"Hotels API failed: {e}")
        return {"hotels": [], "error": str(e)}
    
    hotels = [
        {
            "name": item.get("name"),
            "rating": item.get("rating", 0),
            "address": item.get("formatted_address"),
            "price_level": item.get("price_level", 2),
        }
        for item in data.get("results", [])[:5]
    ]
    
    payload = {"hotels": hotels}
    cache_client.set_places(destination, cache_key, payload)
    return payload
