"""
Integration tests for the orchestrator pipeline.
Tests the full generate_itinerary flow with mocked Gemini client.
"""
import pytest
from unittest.mock import patch, MagicMock, PropertyMock

from trip_planner.models import Itinerary, AgentTrace
from trip_planner.services.orchestrator import generate_itinerary, _build_packing_list
from trip_planner.core.exceptions import GeminiError


pytestmark = pytest.mark.django_db


class TestBuildPackingList:
    def test_basic_packing_items(self):
        result = _build_packing_list({}, {})
        assert "Comfortable shoes" in result
        assert "Water bottle" in result

    def test_hot_weather_items(self):
        weather = {"daily": [{"high_c": 35, "low_c": 25, "precipitation_chance": 0}]}
        result = _build_packing_list(weather, {})
        assert "Sunscreen" in result
        assert "Sunhat" in result

    def test_cold_weather_items(self):
        weather = {"daily": [{"high_c": 5, "low_c": -2, "precipitation_chance": 0}]}
        result = _build_packing_list(weather, {})
        assert "Warm jacket" in result
        assert "Layers" in result

    def test_rainy_weather_items(self):
        weather = {"daily": [{"high_c": 20, "low_c": 15, "precipitation_chance": 0.6}]}
        result = _build_packing_list(weather, {})
        assert "Rain jacket" in result
        assert "Umbrella" in result


class TestOrchestratorGeminiUnavailable:
    @patch("trip_planner.services.orchestrator.gemini_client")
    def test_raises_gemini_error_when_unavailable(self, mock_client, sample_trip):
        type(mock_client).is_available = PropertyMock(return_value=False)
        mock_client._error_reason = "No API key"

        itinerary = Itinerary.objects.create(request_json=sample_trip)
        with pytest.raises(GeminiError, match="No API key"):
            generate_itinerary(sample_trip, itinerary)


class TestOrchestratorFullPipeline:
    """Full pipeline test with a mock Gemini client that returns valid JSON."""

    @patch("trip_planner.services.orchestrator.gemini_client")
    def test_full_pipeline_produces_valid_response(self, mock_global_client, sample_trip, mock_gemini_client):
        # Replace the global gemini_client with our mock
        type(mock_global_client).is_available = PropertyMock(return_value=True)
        mock_global_client.generate_content = mock_gemini_client.generate_content

        # Also mock the external services to avoid network calls
        with patch("trip_planner.agents.research.get_hotels") as mock_hotels, \
             patch("trip_planner.agents.research.get_travel_time_minutes") as mock_travel, \
             patch("trip_planner.agents.weather.get_weather") as mock_weather, \
             patch("trip_planner.agents.attractions.get_attractions") as mock_attractions, \
             patch("trip_planner.services.gemini.generate_validated") as mock_gen_validated:

            mock_hotels.return_value = {"hotels": [{"name": "Test Hotel", "rating": 4.0}]}
            mock_travel.return_value = {"travel_time_minutes": 60}
            mock_weather.return_value = {
                "daily": [{"date": sample_trip["start_date"], "high_c": 22, "low_c": 12,
                           "precipitation_chance": 0.1}],
                "forecast_source": "mock",
                "overview": "Sunny and mild"
            }
            mock_attractions.return_value = {
                "attractions": [{"name": "Eiffel Tower", "rating": 4.7}]
            }

            # generate_validated returns (data, drafts, issues)
            def mock_gen_val(client, system, user, schema):
                from trip_planner.core.utils import best_effort_json
                raw = client.generate_content(system + " " + user)
                data = best_effort_json(raw)
                return data, [], []

            mock_gen_validated.side_effect = mock_gen_val

            itinerary = Itinerary.objects.create(request_json=sample_trip)
            result = generate_itinerary(sample_trip, itinerary)

            # Verify response structure
            assert "itinerary_id" in result
            assert "summary" in result
            assert "days" in result
            assert "weather" in result
            assert "attractions" in result
            assert "packing_list" in result
            assert "budget" in result
            assert "validation" in result
            assert "travel_options" in result
            assert "generated_at" in result

            # Verify traces were created
            traces = AgentTrace.objects.filter(itinerary=itinerary)
            assert traces.count() > 0
            agent_names = set(t.agent_name for t in traces)
            assert "planner" in agent_names
            assert "weather" in agent_names
            assert "validator" in agent_names

    @patch("trip_planner.services.orchestrator.gemini_client")
    def test_pipeline_with_unknown_location(self, mock_global_client, unknown_location_trip, mock_gemini_client):
        type(mock_global_client).is_available = PropertyMock(return_value=True)
        mock_global_client.generate_content = mock_gemini_client.generate_content

        with patch("trip_planner.agents.research.get_hotels") as mock_hotels, \
             patch("trip_planner.agents.research.get_travel_time_minutes") as mock_travel, \
             patch("trip_planner.agents.weather.get_weather") as mock_weather, \
             patch("trip_planner.agents.attractions.get_attractions") as mock_attractions, \
             patch("trip_planner.services.gemini.generate_validated") as mock_gen_validated:

            mock_hotels.return_value = {"hotels": []}
            mock_travel.return_value = {"travel_time_minutes": 20}
            mock_weather.return_value = {"daily": [], "forecast_source": "stub"}
            mock_attractions.return_value = {"attractions": []}

            def mock_gen_val(client, system, user, schema):
                from trip_planner.core.utils import best_effort_json
                raw = client.generate_content(system + " " + user)
                data = best_effort_json(raw)
                return data, [], []

            mock_gen_validated.side_effect = mock_gen_val

            itinerary = Itinerary.objects.create(request_json=unknown_location_trip)
            result = generate_itinerary(unknown_location_trip, itinerary)

            # Should succeed even with unknown location
            assert "days" in result
            assert "itinerary_id" in result
            assert result["itinerary_id"] == str(itinerary.id)
