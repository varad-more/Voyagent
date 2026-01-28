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
        resp = await client.get(
            "https://maps.googleapis.com/maps/api/place/textsearch/json",
            params={"query": query, "key": settings.google_places_api_key},
        )
        resp.raise_for_status()
        data = resp.json()

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
