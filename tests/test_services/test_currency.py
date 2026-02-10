"""
Tests for the currency exchange service.
"""
import pytest
from unittest.mock import patch, MagicMock

from trip_planner.services.currency import get_currency_rate, convert_amount


pytestmark = pytest.mark.django_db


class TestSameCurrency:
    def test_same_currency_returns_one(self):
        result = get_currency_rate("USD", "USD")
        assert result == {"rate": 1.0}

    def test_same_currency_case_insensitive(self):
        result = get_currency_rate("usd", "USD")
        assert result == {"rate": 1.0}


class TestCurrencyCache:
    @patch("trip_planner.services.currency.cache_client")
    def test_cached_rate_returned(self, mock_cache):
        mock_cache.get_currency_rate.return_value = 0.85
        result = get_currency_rate("USD", "EUR")
        assert result == {"rate": 0.85}


class TestCurrencyNoAPIKey:
    @patch("trip_planner.services.currency.settings")
    @patch("trip_planner.services.currency.cache_client")
    def test_no_api_key_returns_one(self, mock_cache, mock_settings):
        mock_cache.get_currency_rate.return_value = None
        mock_settings.CURRENCY_API_KEY = ""

        result = get_currency_rate("USD", "EUR")
        assert result == {"rate": 1.0}


class TestCurrencyAPICall:
    @patch("trip_planner.services.currency.requests")
    @patch("trip_planner.services.currency.settings")
    @patch("trip_planner.services.currency.cache_client")
    def test_api_success(self, mock_cache, mock_settings, mock_requests):
        mock_cache.get_currency_rate.return_value = None
        mock_settings.CURRENCY_API_KEY = "fake-key"

        response = MagicMock()
        response.raise_for_status.return_value = None
        response.json.return_value = {"rates": {"EUR": 0.92}}
        mock_requests.get.return_value = response

        result = get_currency_rate("USD", "EUR")
        assert result == {"rate": 0.92}
        mock_cache.set_currency_rate.assert_called_once()

    @patch("trip_planner.services.currency.requests")
    @patch("trip_planner.services.currency.settings")
    @patch("trip_planner.services.currency.cache_client")
    def test_api_error_returns_one(self, mock_cache, mock_settings, mock_requests):
        mock_cache.get_currency_rate.return_value = None
        mock_settings.CURRENCY_API_KEY = "fake-key"
        mock_requests.get.side_effect = Exception("Timeout")

        result = get_currency_rate("USD", "JPY")
        assert result == {"rate": 1.0}


class TestConvertAmount:
    def test_same_currency(self):
        assert convert_amount(100.0, "USD", "USD") == 100.0

    @patch("trip_planner.services.currency.get_currency_rate")
    def test_conversion(self, mock_rate):
        mock_rate.return_value = {"rate": 0.85}
        result = convert_amount(100.0, "USD", "EUR")
        assert result == 85.0

    @patch("trip_planner.services.currency.get_currency_rate")
    def test_conversion_rounding(self, mock_rate):
        mock_rate.return_value = {"rate": 0.333}
        result = convert_amount(100.0, "USD", "XYZ")
        assert result == 33.3
