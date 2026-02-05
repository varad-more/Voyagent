"""
External cache model for API response caching.
"""
from django.db import models
from django.utils import timezone


class ExternalCache(models.Model):
    """
    Database-backed cache for external API responses.
    """
    cache_key = models.CharField(max_length=512, unique=True, db_index=True)
    source = models.CharField(max_length=64, db_index=True)
    payload_json = models.JSONField()
    expires_at = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "external_cache"
        verbose_name_plural = "External Cache Entries"

    def __str__(self):
        return f"{self.source}:{self.cache_key[:50]}"

    @property
    def is_expired(self) -> bool:
        return timezone.now() > self.expires_at

    @classmethod
    def get_valid(cls, cache_key: str):
        """Get a non-expired cache entry."""
        try:
            entry = cls.objects.get(cache_key=cache_key)
            if not entry.is_expired:
                return entry.payload_json
        except cls.DoesNotExist:
            pass
        return None

    @classmethod
    def set_cache(cls, cache_key: str, source: str, payload: dict, ttl_seconds: int):
        """Set or update a cache entry."""
        expires_at = timezone.now() + timezone.timedelta(seconds=ttl_seconds)
        cls.objects.update_or_create(
            cache_key=cache_key,
            defaults={"source": source, "payload_json": payload, "expires_at": expires_at}
        )

    @classmethod
    def cleanup_expired(cls):
        """Remove expired entries."""
        return cls.objects.filter(expires_at__lt=timezone.now()).delete()
