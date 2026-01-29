from __future__ import annotations

from typing import Any

import httpx

from app.core.cache import CacheClient
from app.core.config import get_settings


async def _stub_places(destination: str) -> dict[str, Any]:
    return {
        "attractions": [
            {
                "name": f"{destination} Old Town Walk",
                "reason": "High-rated historic district with flexible timing.",
                "score": 0.86,
                "distance_km": 1.8,
                "categories": ["historic", "walkable"],
                "address": None,
            },
            {
                "name": f"{destination} Riverside Park",
                "reason": "Great for downtime and scenic photos.",
                "score": 0.78,
                "distance_km": 2.5,
                "categories": ["nature", "relax"],
                "address": None,
            },
            {
                "name": f"{destination} Modern Art Museum",
                "reason": "Indoor option in case of rain.",
                "score": 0.73,
                "distance_km": 3.1,
                "categories": ["museum", "indoor"],
                "address": None,
            },
        ]
    }


async def get_attractions(
    *,
    destination: str,
    interests: list[str],
    session,
) -> dict[str, Any]:
    settings = get_settings()
    cache = CacheClient()
    interest_key = "-".join(sorted(interests)) if interests else "general"
    cache_key = f"places:{destination}:{interest_key}"
    cached = await cache.get(cache_key, session)
    if cached:
        return cached

    if not settings.google_places_api_key:
        payload = await _stub_places(destination)
        await cache.set(cache_key, "google_places", payload, settings.cache_ttl_places_seconds, session)
        return payload

    query = f"top attractions in {destination}"
    if interests:
        query = f"{', '.join(interests)} in {destination}"

    async with httpx.AsyncClient(timeout=20) as client:
        try:
            resp = await client.get(
                "https://maps.googleapis.com/maps/api/place/textsearch/json",
                params={"query": query, "key": settings.google_places_api_key},
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            logger.error("google_places_api_failed", error=str(exc))
            payload = await _stub_places(destination)
            await cache.set(cache_key, "google_places", payload, settings.cache_ttl_places_seconds, session)
            return payload

    attractions = []
    for item in data.get("results", [])[:12]:
        rating = item.get("rating", 3.5)
        score = min(1.0, max(0.1, rating / 5))
        attractions.append(
            {
                "name": item.get("name"),
                "reason": item.get("types", ["attraction"])[0].replace("_", " ").title(),
                "score": score,
                "distance_km": 2.0,
                "categories": item.get("types", []),
                "address": item.get("formatted_address"),
            }
        )

    payload = {"attractions": attractions}
    await cache.set(cache_key, "google_places", payload, settings.cache_ttl_places_seconds, session)
    return payload


async def get_hotels(
    *,
    destination: str,
    comfort_level: str,  # luxury, moderate, budget
    session,
) -> dict[str, Any]:
    settings = get_settings()
    cache = CacheClient()
    cache_key = f"hotels:{destination}:{comfort_level}"
    cached = await cache.get(cache_key, session)
    if cached:
        return cached

    if not settings.google_places_api_key:
        # Stub implementation
        return {
            "hotels": [
                {
                    "name": f"{destination} Grand Hotel ({comfort_level.title()})",
                    "rating": 4.5,
                    "address": "Downtown",
                    "price_level": comfort_level,
                },
                {
                    "name": f"{destination} City Stay ({comfort_level.title()})",
                    "rating": 4.0,
                    "address": "City Center",
                    "price_level": comfort_level,
                }
            ]
        }

    # Map comfort level to price query/keywords
    keyword = "hotel"
    if comfort_level == "luxury":
        keyword = "5 star hotel luxury"
    elif comfort_level == "budget":
        keyword = "cheap hotel hostel"
    else:
        keyword = "3 star hotel"

    query = f"{keyword} in {destination}"

    async with httpx.AsyncClient(timeout=20) as client:
        try:
            resp = await client.get(
                "https://maps.googleapis.com/maps/api/place/textsearch/json",
                params={"query": query, "key": settings.google_places_api_key},
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            return {"hotels": [], "error": str(exc)}

    hotels = []
    for item in data.get("results", [])[:5]:
        hotels.append(
            {
                "name": item.get("name"),
                "rating": item.get("rating", 0),
                "address": item.get("formatted_address"),
                "price_level": item.get("price_level", 2),
                "place_id": item.get("place_id"),
            }
        )

    payload = {"hotels": hotels}
    await cache.set(cache_key, "google_places_hotels", payload, settings.cache_ttl_places_seconds, session)
    return payload
