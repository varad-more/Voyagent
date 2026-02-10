"""
Tests for the travel time calculation service.
"""
import pytest
from unittest.mock import patch, MagicMock

from trip_planner.services.travel_time import get_travel_time_minutes, _parse_coords


pytestmark = pytest.mark.django_db


class TestParseCoords:
    def test_valid_coords(self):
        assert _parse_coords("33.4484, -112.0740") == (33.4484, -112.0740)

    def test_no_comma(self):
        assert _parse_coords("invalid") is None

    def test_non_numeric(self):
        assert _parse_coords("abc, def") is None

    def test_empty_string(self):
        assert _parse_coords("") is None


class TestTravelTimeCache:
    @patch("trip_planner.services.travel_time.cache_client")
    def test_cached_result_returned(self, mock_cache):
        mock_cache.get_travel_time.return_value = 42
        result = get_travel_time_minutes("A", "B")
        assert result == {"travel_time_minutes": 42}


class TestTravelTimeGoogleAPI:
    @patch("trip_planner.services.travel_time.requests")
    @patch("trip_planner.services.travel_time.settings")
    @patch("trip_planner.services.travel_time.cache_client")
    def test_google_api_success(self, mock_cache, mock_settings, mock_requests):
        mock_cache.get_travel_time.return_value = None
        mock_settings.DISTANCE_MATRIX_API_KEY = "fake-key"

        response = MagicMock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "rows": [{
                "elements": [{
                    "status": "OK",
                    "duration": {"value": 5400}  # 90 minutes
                }]
            }]
        }
        mock_requests.get.return_value = response

        result = get_travel_time_minutes("Phoenix, AZ", "Tucson, AZ")
        assert result == {"travel_time_minutes": 90}
        mock_cache.set_travel_time.assert_called_once()

    @patch("trip_planner.services.travel_time.requests")
    @patch("trip_planner.services.travel_time.settings")
    @patch("trip_planner.services.travel_time.cache_client")
    def test_google_api_error_falls_back(self, mock_cache, mock_settings, mock_requests):
        mock_cache.get_travel_time.return_value = None
        mock_settings.DISTANCE_MATRIX_API_KEY = "fake-key"
        mock_requests.get.side_effect = Exception("Network error")

        # No coords, so no OSRM fallback either → default
        result = get_travel_time_minutes("City A", "City B")
        assert result == {"travel_time_minutes": 20}


class TestTravelTimeDefaultFallback:
    @patch("trip_planner.services.travel_time.settings")
    @patch("trip_planner.services.travel_time.cache_client")
    def test_no_api_key_returns_default(self, mock_cache, mock_settings):
        mock_cache.get_travel_time.return_value = None
        mock_settings.DISTANCE_MATRIX_API_KEY = ""

        result = get_travel_time_minutes("Unknown A", "Unknown B")
        assert result == {"travel_time_minutes": 20}
        mock_cache.set_travel_time.assert_called_once_with("Unknown A", "Unknown B", 20)


class TestTravelTimeOSRM:
    @patch("trip_planner.services.travel_time.requests")
    @patch("trip_planner.services.travel_time.settings")
    @patch("trip_planner.services.travel_time.cache_client")
    def test_osrm_fallback_with_coords(self, mock_cache, mock_settings, mock_requests):
        mock_cache.get_travel_time.return_value = None
        mock_settings.DISTANCE_MATRIX_API_KEY = ""

        response = MagicMock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "routes": [{"duration": 3600}]  # 60 minutes
        }
        mock_requests.get.return_value = response

        result = get_travel_time_minutes("33.4484, -112.0740", "32.2226, -110.9747")
        assert result == {"travel_time_minutes": 60}
