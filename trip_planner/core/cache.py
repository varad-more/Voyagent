"""
Caching utilities with dual-layer support (Redis + Database).
"""
import logging
import hashlib
from typing import Any, Optional
from django.conf import settings
from django.core.cache import cache as django_cache

logger = logging.getLogger(__name__)


class CacheClient:
    """Dual-layer cache client: Redis (optional) + Database fallback."""
    
    @staticmethod
    def _make_key(prefix: str, *args) -> str:
        """Generate a cache key."""
        key_parts = [prefix] + [str(arg) for arg in args if arg]
        raw_key = ":".join(key_parts)
        if len(raw_key) > 200:
            hash_suffix = hashlib.md5(raw_key.encode()).hexdigest()[:16]
            return f"{prefix}:{hash_suffix}"
        return raw_key
    
    @classmethod
    def get(cls, key: str, source: str = "general") -> Optional[Any]:
        """Get value from cache (Django cache first, then DB)."""
        # Lazy import to avoid circular dependency
        from trip_planner.models import ExternalCache
        
        # Try Django cache
        try:
            value = django_cache.get(key)
            if value is not None:
                return value
        except Exception as e:
            logger.warning(f"Django cache get failed: {e}")
        
        # Try database cache
        try:
            value = ExternalCache.get_valid(key)
            if value is not None:
                # Populate Django cache
                try:
                    django_cache.set(key, value, timeout=3600)
                except Exception:
                    pass
                return value
        except Exception as e:
            logger.warning(f"DB cache get failed: {e}")
        
        return None
    
    @classmethod
    def set(cls, key: str, value: Any, ttl: int, source: str = "general") -> bool:
        """Set value in both caches."""
        from trip_planner.models import ExternalCache
        
        success = True
        
        # Django cache
        try:
            django_cache.set(key, value, timeout=ttl)
        except Exception as e:
            logger.warning(f"Django cache set failed: {e}")
            success = False
        
        # Database cache
        try:
            payload = value if isinstance(value, dict) else {"value": value}
            ExternalCache.set_cache(key, source, payload, ttl)
        except Exception as e:
            logger.warning(f"DB cache set failed: {e}")
            success = False
        
        return success
    
    # Convenience methods
    @classmethod
    def get_weather(cls, destination: str, date_range: str) -> Optional[dict]:
        key = cls._make_key("weather", destination, date_range)
        return cls.get(key, "weather")
    
    @classmethod
    def set_weather(cls, destination: str, date_range: str, data: dict, ttl: int = None) -> bool:
        key = cls._make_key("weather", destination, date_range)
        ttl = ttl or settings.CACHE_TTL_WEATHER
        return cls.set(key, data, ttl, "weather")
    
    @classmethod
    def get_places(cls, destination: str, query: str) -> Optional[dict]:
        key = cls._make_key("places", destination, query)
        return cls.get(key, "places")
    
    @classmethod
    def set_places(cls, destination: str, query: str, data: dict, ttl: int = None) -> bool:
        key = cls._make_key("places", destination, query)
        ttl = ttl or settings.CACHE_TTL_PLACES
        return cls.set(key, data, ttl, "places")
    
    @classmethod
    def get_travel_time(cls, origin: str, dest: str) -> Optional[int]:
        key = cls._make_key("travel", origin, dest)
        result = cls.get(key, "travel")
        return result.get("minutes") if result else None
    
    @classmethod
    def set_travel_time(cls, origin: str, dest: str, minutes: int, ttl: int = None) -> bool:
        key = cls._make_key("travel", origin, dest)
        ttl = ttl or settings.CACHE_TTL_TRAVEL
        return cls.set(key, {"minutes": minutes}, ttl, "travel")
    
    @classmethod
    def get_currency_rate(cls, base: str, target: str) -> Optional[float]:
        key = cls._make_key("currency", base, target)
        result = cls.get(key, "currency")
        return result.get("rate") if result else None
    
    @classmethod
    def set_currency_rate(cls, base: str, target: str, rate: float) -> bool:
        key = cls._make_key("currency", base, target)
        return cls.set(key, {"rate": rate}, settings.CACHE_TTL_CURRENCY, "currency")


cache_client = CacheClient()
