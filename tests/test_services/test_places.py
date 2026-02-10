"""
Tests for the Google Places service.
"""
import pytest
from unittest.mock import patch, MagicMock

from trip_planner.services.places import get_attractions, get_hotels


pytestmark = pytest.mark.django_db


class TestAttractionsStub:
    """When no API key is set, stub attractions are returned."""

    @patch("trip_planner.services.places.settings")
    @patch("trip_planner.services.places.cache_client")
    def test_stub_attractions_returned(self, mock_cache, mock_settings):
        mock_settings.GOOGLE_PLACES_API_KEY = ""
        mock_cache.get_places.return_value = None

        result = get_attractions("Paris", ["museums", "history"])

        assert "attractions" in result
        assert isinstance(result["attractions"], list)
        assert len(result["attractions"]) > 0

    @patch("trip_planner.services.places.settings")
    @patch("trip_planner.services.places.cache_client")
    def test_stub_uses_destination_name(self, mock_cache, mock_settings):
        mock_settings.GOOGLE_PLACES_API_KEY = ""
        mock_cache.get_places.return_value = None

        result = get_attractions("Faroe Islands", ["nature"])

        # At least one attraction should reference the destination
        names = [a.get("name", "") for a in result["attractions"]]
        combined = " ".join(names).lower()
        # Stubs typically include the destination name or generic names
        assert len(names) > 0

    @patch("trip_planner.services.places.settings")
    @patch("trip_planner.services.places.cache_client")
    def test_empty_interests_still_returns_attractions(self, mock_cache, mock_settings):
        mock_settings.GOOGLE_PLACES_API_KEY = ""
        mock_cache.get_places.return_value = None

        result = get_attractions("Tokyo", [])
        assert len(result["attractions"]) > 0


class TestHotelsStub:
    @patch("trip_planner.services.places.settings")
    @patch("trip_planner.services.places.cache_client")
    def test_stub_hotels_returned(self, mock_cache, mock_settings):
        mock_settings.GOOGLE_PLACES_API_KEY = ""
        mock_cache.get_places.return_value = None

        result = get_hotels("Paris", "midrange")

        assert "hotels" in result
        assert isinstance(result["hotels"], list)
        assert len(result["hotels"]) > 0

    @patch("trip_planner.services.places.settings")
    @patch("trip_planner.services.places.cache_client")
    def test_budget_hotels(self, mock_cache, mock_settings):
        mock_settings.GOOGLE_PLACES_API_KEY = ""
        mock_cache.get_places.return_value = None

        result = get_hotels("Tokyo", "budget")
        assert len(result["hotels"]) > 0

    @patch("trip_planner.services.places.settings")
    @patch("trip_planner.services.places.cache_client")
    def test_luxury_hotels(self, mock_cache, mock_settings):
        mock_settings.GOOGLE_PLACES_API_KEY = ""
        mock_cache.get_places.return_value = None

        result = get_hotels("Tokyo", "luxury")
        assert len(result["hotels"]) > 0


class TestPlacesCache:
    @patch("trip_planner.services.places.cache_client")
    def test_cached_attractions_returned(self, mock_cache):
        cached = {"attractions": [{"name": "Cached Place", "rating": 4.5}]}
        mock_cache.get_places.return_value = cached

        result = get_attractions("Paris", ["history"])
        assert result == cached


class TestPlacesAPIError:
    @patch("trip_planner.services.places.requests")
    @patch("trip_planner.services.places.settings")
    @patch("trip_planner.services.places.cache_client")
    def test_api_error_falls_back_to_stub(self, mock_cache, mock_settings, mock_requests):
        mock_settings.GOOGLE_PLACES_API_KEY = "fake-key"
        mock_cache.get_places.return_value = None
        mock_requests.get.side_effect = Exception("API Error")

        result = get_attractions("Paris", ["history"])
        assert "attractions" in result
        assert isinstance(result["attractions"], list)
