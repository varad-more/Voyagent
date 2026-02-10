"""
Tests for the WeatherAgent.
"""
import pytest
from unittest.mock import patch

from trip_planner.agents.weather import WeatherAgent


pytestmark = pytest.mark.django_db


class TestWeatherAgentStub:
    @patch("trip_planner.agents.weather.get_weather")
    def test_stub_output_structure(self, mock_get_weather, sample_trip, mock_gemini_unavailable):
        mock_get_weather.return_value = {
            "daily": [
                {"date": sample_trip["start_date"], "temp_high": 22, "precipitation_chance": 0.1}
            ],
            "forecast_source": "stub"
        }

        agent = WeatherAgent(gemini_client=mock_gemini_unavailable)
        result = agent.run(trip=sample_trip)

        assert result.data is not None
        assert "weather" in result.data
        assert "adjustments" in result.data
        assert isinstance(result.data["adjustments"], list)

    @patch("trip_planner.agents.weather.get_weather")
    def test_high_rain_adds_indoor_suggestion(self, mock_get_weather, sample_trip, mock_gemini_unavailable):
        mock_get_weather.return_value = {
            "daily": [
                {"date": sample_trip["start_date"], "temp_high": 15, "precipitation_chance": 0.8}
            ],
            "forecast_source": "stub"
        }

        agent = WeatherAgent(gemini_client=mock_gemini_unavailable)
        result = agent.run(trip=sample_trip)

        adjustments_text = " ".join(result.data["adjustments"]).lower()
        assert "indoor" in adjustments_text or "rain" in adjustments_text

    @patch("trip_planner.agents.weather.get_weather")
    def test_stub_includes_gemini_disabled(self, mock_get_weather, sample_trip, mock_gemini_unavailable):
        mock_get_weather.return_value = {"daily": [], "forecast_source": "stub"}
        agent = WeatherAgent(gemini_client=mock_gemini_unavailable)
        result = agent.run(trip=sample_trip)
        assert "gemini_disabled" in result.issues

    @patch("trip_planner.agents.weather.get_weather")
    def test_unknown_location(self, mock_get_weather, unknown_location_trip, mock_gemini_unavailable):
        mock_get_weather.return_value = {"daily": [], "forecast_source": "stub"}
        agent = WeatherAgent(gemini_client=mock_gemini_unavailable)
        result = agent.run(trip=unknown_location_trip)
        assert result.data is not None
        assert "weather" in result.data
