"""
Tests for the PlannerAgent.
"""
import pytest
from datetime import date, timedelta

from trip_planner.agents.planner import PlannerAgent


class TestPlannerAgentStub:
    """When Gemini is unavailable, the agent should produce valid stub output."""

    def test_stub_output_structure(self, sample_trip, mock_gemini_unavailable):
        agent = PlannerAgent(gemini_client=mock_gemini_unavailable)
        result = agent.run(trip=sample_trip)

        assert result.data is not None
        assert "summary" in result.data
        assert "days" in result.data
        assert isinstance(result.data["days"], list)

    def test_stub_has_correct_day_count(self, sample_trip, mock_gemini_unavailable):
        agent = PlannerAgent(gemini_client=mock_gemini_unavailable)
        result = agent.run(trip=sample_trip)

        start = date.fromisoformat(sample_trip["start_date"])
        end = date.fromisoformat(sample_trip["end_date"])
        expected_days = (end - start).days + 1

        assert len(result.data["days"]) == expected_days

    def test_stub_day_has_required_fields(self, sample_trip, mock_gemini_unavailable):
        agent = PlannerAgent(gemini_client=mock_gemini_unavailable)
        result = agent.run(trip=sample_trip)

        day = result.data["days"][0]
        assert "date" in day
        assert "theme" in day
        assert "must_do" in day
        assert "optional_stops" in day

    def test_stub_includes_gemini_disabled_issue(self, sample_trip, mock_gemini_unavailable):
        agent = PlannerAgent(gemini_client=mock_gemini_unavailable)
        result = agent.run(trip=sample_trip)
        assert "gemini_disabled" in result.issues

    def test_stub_with_unknown_location(self, unknown_location_trip, mock_gemini_unavailable):
        agent = PlannerAgent(gemini_client=mock_gemini_unavailable)
        result = agent.run(trip=unknown_location_trip)
        assert "Tórshavn" in result.data["summary"] or "Faroe" in result.data["summary"]
        assert len(result.data["days"]) > 0

    def test_stub_with_multi_city(self, multi_city_trip, mock_gemini_unavailable):
        agent = PlannerAgent(gemini_client=mock_gemini_unavailable)
        result = agent.run(trip=multi_city_trip)
        assert len(result.data["days"]) > 0


class TestPlannerAgentNoClient:
    def test_no_gemini_client(self, sample_trip):
        agent = PlannerAgent(gemini_client=None)
        result = agent.run(trip=sample_trip)
        assert result.data is not None
        assert "days" in result.data
