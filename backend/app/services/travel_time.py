from __future__ import annotations

from typing import Any

import httpx

from app.core.cache import CacheClient
from app.core.config import get_settings


def _parse_coordinates(value: str) -> tuple[float, float] | None:
    if "," not in value:
        return None
    parts = [part.strip() for part in value.split(",", maxsplit=1)]
    try:
        return float(parts[0]), float(parts[1])
    except ValueError:
        return None


async def get_travel_time_minutes(
    *,
    origin: str,
    destination: str,
    session,
) -> dict[str, Any]:
    settings = get_settings()
    cache = CacheClient()
    cache_key = f"travel:{origin}:{destination}"
    cached = await cache.get(cache_key, session)
    if cached:
        return cached

    if settings.distance_matrix_api_key:
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    "https://maps.googleapis.com/maps/api/distancematrix/json",
                    params={
                        "origins": origin,
                        "destinations": destination,
                        "key": settings.distance_matrix_api_key,
                        "units": "metric",
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                rows = data.get("rows", [])
                duration = rows[0]["elements"][0]["duration"]["value"] / 60 if rows else 20
                payload = {"travel_time_minutes": int(duration)}
                await cache.set(
                    cache_key, "distance_matrix", payload, settings.cache_ttl_travel_seconds, session
                )
                return payload
        except Exception:
            pass  # Fallback to OSRM or default

    origin_coords = _parse_coordinates(origin)
    dest_coords = _parse_coordinates(destination)
    if origin_coords and dest_coords:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"https://router.project-osrm.org/route/v1/driving/"
                    f"{origin_coords[1]},{origin_coords[0]};{dest_coords[1]},{dest_coords[0]}",
                    params={"overview": "false"},
                )
                resp.raise_for_status()
                data = resp.json()
                routes = data.get("routes", [])
                duration = routes[0]["duration"] / 60 if routes else 20
                payload = {"travel_time_minutes": int(duration)}
                await cache.set(
                    cache_key, "osrm", payload, settings.cache_ttl_travel_seconds, session
                )
                return payload
        except Exception:
            pass  # Fallback to default

    payload = {"travel_time_minutes": 20}
    await cache.set(
        cache_key, "fallback", payload, settings.cache_ttl_travel_seconds, session
    )
    return payload
