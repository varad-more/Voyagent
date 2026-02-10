"""
Tests for the AttractionsAgent.
"""
import pytest
from unittest.mock import patch

from trip_planner.agents.attractions import AttractionsAgent


pytestmark = pytest.mark.django_db


class TestAttractionsAgentStub:
    @patch("trip_planner.agents.attractions.get_attractions")
    def test_stub_output_structure(self, mock_get, sample_trip, mock_gemini_unavailable):
        mock_get.return_value = {
            "attractions": [
                {"name": "Eiffel Tower", "rating": 4.7, "types": ["landmark"]},
                {"name": "Louvre Museum", "rating": 4.8, "types": ["museum"]},
            ]
        }

        agent = AttractionsAgent(gemini_client=mock_gemini_unavailable)
        result = agent.run(trip=sample_trip)

        assert result.data is not None
        assert "attractions" in result.data
        assert isinstance(result.data["attractions"], list)
        assert len(result.data["attractions"]) == 2

    @patch("trip_planner.agents.attractions.get_attractions")
    def test_stub_with_no_attractions(self, mock_get, sample_trip, mock_gemini_unavailable):
        mock_get.return_value = {"attractions": []}
        agent = AttractionsAgent(gemini_client=mock_gemini_unavailable)
        result = agent.run(trip=sample_trip)
        assert result.data["attractions"] == []

    @patch("trip_planner.agents.attractions.get_attractions")
    def test_unknown_location(self, mock_get, unknown_location_trip, mock_gemini_unavailable):
        mock_get.return_value = {"attractions": [{"name": "Generic Attraction"}]}
        agent = AttractionsAgent(gemini_client=mock_gemini_unavailable)
        result = agent.run(trip=unknown_location_trip)
        assert len(result.data["attractions"]) > 0
