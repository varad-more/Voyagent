"""
Tests for the weather service (OpenWeather API wrapper).
"""
import pytest
from datetime import date, timedelta
from unittest.mock import patch, MagicMock

from trip_planner.services.weather import get_weather


pytestmark = pytest.mark.django_db


def _future(days=30):
    return date.today() + timedelta(days=days)


class TestWeatherServiceStub:
    """When no API key is set, the service should return stub data."""

    @patch("trip_planner.services.weather.settings")
    @patch("trip_planner.services.weather.cache_client")
    def test_stub_returned_when_no_api_key(self, mock_cache, mock_settings):
        mock_settings.OPENWEATHER_API_KEY = ""
        mock_cache.get_weather.return_value = None

        result = get_weather("Unknown Island", _future(30), _future(32))

        assert "daily" in result
        assert isinstance(result["daily"], list)
        assert result.get("forecast_source") == "stub"

    @patch("trip_planner.services.weather.settings")
    @patch("trip_planner.services.weather.cache_client")
    def test_stub_contains_correct_date_count(self, mock_cache, mock_settings):
        mock_settings.OPENWEATHER_API_KEY = ""
        mock_cache.get_weather.return_value = None

        start = _future(30)
        end = _future(32)
        result = get_weather("Paris", start, end)

        # Should have entries for each day (3 days)
        assert len(result["daily"]) == 3


class TestWeatherServiceCache:
    """Cached weather data should be returned without hitting the API."""

    @patch("trip_planner.services.weather.cache_client")
    def test_cached_data_returned(self, mock_cache):
        cached = {"daily": [{"date": "2026-04-01", "temp_high": 22}], "forecast_source": "cached"}
        mock_cache.get_weather.return_value = cached

        result = get_weather("Paris", _future(30), _future(32))
        assert result == cached


class TestWeatherServiceAPI:
    """Test API call path with mocked requests."""

    @patch("trip_planner.services.weather.requests")
    @patch("trip_planner.services.weather.settings")
    @patch("trip_planner.services.weather.cache_client")
    def test_api_error_falls_back_to_stub(self, mock_cache, mock_settings, mock_requests):
        mock_settings.OPENWEATHER_API_KEY = "fake-key"
        mock_cache.get_weather.return_value = None
        mock_requests.get.side_effect = Exception("Network error")

        result = get_weather("Paris", _future(30), _future(32))

        # Should return stub data, not crash
        assert "daily" in result
        assert isinstance(result["daily"], list)

    @patch("trip_planner.services.weather.requests")
    @patch("trip_planner.services.weather.settings")
    @patch("trip_planner.services.weather.cache_client")
    def test_unknown_location_returns_stub(self, mock_cache, mock_settings, mock_requests):
        mock_settings.OPENWEATHER_API_KEY = "fake-key"
        mock_cache.get_weather.return_value = None
        # Simulate geocode returning empty results
        geo_resp = MagicMock()
        geo_resp.raise_for_status.return_value = None
        geo_resp.json.return_value = []
        mock_requests.get.return_value = geo_resp

        result = get_weather("Xyzzyville Nowhere", _future(30), _future(32))
        assert "daily" in result
