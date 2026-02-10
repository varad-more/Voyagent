"""
Tests for the FoodAgent.
"""
import pytest

from trip_planner.agents.food import FoodAgent


class TestFoodAgentStub:
    def test_stub_output_structure(self, sample_trip, sample_scheduler_output, mock_gemini_unavailable):
        agent = FoodAgent(gemini_client=mock_gemini_unavailable)
        result = agent.run(trip=sample_trip, scheduler_output=sample_scheduler_output)

        assert result.data is not None
        assert "days" in result.data
        assert isinstance(result.data["days"], list)
        assert len(result.data["days"]) == len(sample_scheduler_output["days"])

    def test_stub_has_three_meals(self, sample_trip, sample_scheduler_output, mock_gemini_unavailable):
        agent = FoodAgent(gemini_client=mock_gemini_unavailable)
        result = agent.run(trip=sample_trip, scheduler_output=sample_scheduler_output)

        day = result.data["days"][0]
        assert "meals" in day
        assert len(day["meals"]) == 3  # breakfast, lunch, dinner

    def test_stub_meal_fields(self, sample_trip, sample_scheduler_output, mock_gemini_unavailable):
        agent = FoodAgent(gemini_client=mock_gemini_unavailable)
        result = agent.run(trip=sample_trip, scheduler_output=sample_scheduler_output)

        meal = result.data["days"][0]["meals"][0]
        for field in ["time", "name", "cuisine", "location", "estimated_cost"]:
            assert field in meal, f"Missing meal field: {field}"

    def test_stub_respects_dietary_restrictions(self, sample_trip, sample_scheduler_output, mock_gemini_unavailable):
        agent = FoodAgent(gemini_client=mock_gemini_unavailable)
        result = agent.run(trip=sample_trip, scheduler_output=sample_scheduler_output)

        meal = result.data["days"][0]["meals"][0]
        # The stub includes dietary_fit from the trip preferences
        assert "dietary_fit" in meal

    def test_empty_scheduler(self, sample_trip, mock_gemini_unavailable):
        agent = FoodAgent(gemini_client=mock_gemini_unavailable)
        result = agent.run(trip=sample_trip, scheduler_output={"days": []})
        assert result.data["days"] == []
