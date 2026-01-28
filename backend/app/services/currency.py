from __future__ import annotations

from typing import Any

import httpx

from app.core.cache import CacheClient
from app.core.config import get_settings


async def get_currency_rate(
    *,
    base: str,
    target: str,
    session,
) -> dict[str, Any]:
    settings = get_settings()
    cache = CacheClient()
    cache_key = f"currency:{base}:{target}"
    cached = await cache.get(cache_key, session)
    if cached:
        return cached

    if not settings.currency_api_key:
        payload = {"rate": 1.0}
        await cache.set(
            cache_key, "stub", payload, settings.cache_ttl_currency_seconds, session
        )
        return payload

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            "https://api.exchangerate.host/latest",
            params={"base": base, "symbols": target, "access_key": settings.currency_api_key},
        )
        resp.raise_for_status()
        data = resp.json()

    rate = data.get("rates", {}).get(target, 1.0)
    payload = {"rate": rate}
    await cache.set(
        cache_key, "exchangerate", payload, settings.cache_ttl_currency_seconds, session
    )
    return payload
