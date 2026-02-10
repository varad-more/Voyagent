"""
Tests for the CacheClient dual-layer caching system.
"""
import pytest
from trip_planner.core.cache import CacheClient


pytestmark = pytest.mark.django_db


class TestCacheKeyGeneration:
    def test_simple_key(self):
        key = CacheClient._make_key("weather", "Paris", "2026-04-01:2026-04-03")
        assert key == "weather:Paris:2026-04-01:2026-04-03"

    def test_empty_args_skipped(self):
        key = CacheClient._make_key("weather", "Paris", None, "")
        assert key == "weather:Paris"

    def test_long_key_gets_hashed(self):
        long_dest = "A" * 250
        key = CacheClient._make_key("weather", long_dest)
        assert len(key) <= 200
        assert key.startswith("weather:")


class TestWeatherCache:
    def test_set_and_get(self):
        data = {"forecast_source": "test", "daily": []}
        CacheClient.set_weather("Paris", "2026-04-01:2026-04-03", data)
        result = CacheClient.get_weather("Paris", "2026-04-01:2026-04-03")
        assert result is not None
        assert result["forecast_source"] == "test"

    def test_miss(self):
        result = CacheClient.get_weather("NowhereVille", "2099-01-01:2099-01-02")
        assert result is None


class TestPlacesCache:
    def test_set_and_get(self):
        data = {"attractions": [{"name": "Test Place"}]}
        CacheClient.set_places("Tokyo", "museums", data)
        result = CacheClient.get_places("Tokyo", "museums")
        assert result is not None
        assert len(result["attractions"]) == 1

    def test_miss(self):
        assert CacheClient.get_places("Missing", "query") is None


class TestTravelTimeCache:
    def test_set_and_get(self):
        CacheClient.set_travel_time("A", "B", 45)
        result = CacheClient.get_travel_time("A", "B")
        assert result == 45

    def test_miss(self):
        assert CacheClient.get_travel_time("X", "Y") is None


class TestCurrencyRateCache:
    def test_set_and_get(self):
        CacheClient.set_currency_rate("USD", "EUR", 0.85)
        result = CacheClient.get_currency_rate("USD", "EUR")
        assert result == 0.85

    def test_miss(self):
        assert CacheClient.get_currency_rate("ABC", "XYZ") is None
