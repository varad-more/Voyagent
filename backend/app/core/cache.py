from __future__ import annotations

import datetime as dt
import json
from typing import Any, Optional

import redis.asyncio as redis
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.cache import ExternalCache


logger = structlog.get_logger(__name__)


class CacheClient:
    def __init__(self) -> None:
        settings = get_settings()
        self.redis_url = settings.redis_url
        self._redis: Optional[redis.Redis] = None

    async def _get_redis(self) -> Optional[redis.Redis]:
        if not self.redis_url:
            return None
        if self._redis is None:
            self._redis = redis.from_url(self.redis_url, decode_responses=True)
        return self._redis

    async def get(self, key: str, session: AsyncSession) -> Optional[dict[str, Any]]:
        redis_client = await self._get_redis()
        if redis_client:
            try:
                cached = await redis_client.get(key)
                if cached:
                    return json.loads(cached)
            except Exception as exc:  # pragma: no cover - redis optional
                logger.warning("redis_get_failed", error=str(exc))

        result = await session.execute(
            select(ExternalCache).where(ExternalCache.cache_key == key)
        )
        row = result.scalar_one_or_none()
        if not row:
            return None
        if row.expires_at < dt.datetime.now(dt.timezone.utc):
            return None
        return row.payload_json

    async def set(
        self, key: str, source: str, payload: dict[str, Any], ttl_seconds: int, session: AsyncSession
    ) -> None:
        expires_at = dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=ttl_seconds)
        redis_client = await self._get_redis()
        if redis_client:
            try:
                await redis_client.set(key, json.dumps(payload), ex=ttl_seconds)
            except Exception as exc:  # pragma: no cover - redis optional
                logger.warning("redis_set_failed", error=str(exc))

        result = await session.execute(
            select(ExternalCache).where(ExternalCache.cache_key == key)
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.payload_json = payload
            existing.expires_at = expires_at
        else:
            session.add(
                ExternalCache(
                    cache_key=key,
                    source=source,
                    payload_json=payload,
                    expires_at=expires_at,
                )
            )
