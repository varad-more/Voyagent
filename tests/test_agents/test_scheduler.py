"""
Tests for the SchedulerAgent.
"""
import pytest

from trip_planner.agents.scheduler import SchedulerAgent


class TestSchedulerAgentStub:
    def test_stub_output_structure(self, sample_trip, sample_planner_output, mock_gemini_unavailable):
        agent = SchedulerAgent(gemini_client=mock_gemini_unavailable)
        result = agent.run(
            trip=sample_trip,
            planner_output=sample_planner_output,
            weather_summary="Sunny, 22°C"
        )

        assert result.data is not None
        assert "days" in result.data
        assert isinstance(result.data["days"], list)
        assert len(result.data["days"]) == len(sample_planner_output["days"])

    def test_stub_day_has_schedule(self, sample_trip, sample_planner_output, mock_gemini_unavailable):
        agent = SchedulerAgent(gemini_client=mock_gemini_unavailable)
        result = agent.run(
            trip=sample_trip,
            planner_output=sample_planner_output,
            weather_summary="Cloudy"
        )

        day = result.data["days"][0]
        assert "schedule" in day
        assert "date" in day
        assert "weather_summary" in day
        assert len(day["schedule"]) > 0

    def test_stub_schedule_block_fields(self, sample_trip, sample_planner_output, mock_gemini_unavailable):
        agent = SchedulerAgent(gemini_client=mock_gemini_unavailable)
        result = agent.run(
            trip=sample_trip,
            planner_output=sample_planner_output,
            weather_summary="Rain"
        )

        block = result.data["days"][0]["schedule"][0]
        required_fields = ["start_time", "end_time", "title", "location", "description", "block_type"]
        for field in required_fields:
            assert field in block, f"Missing field: {field}"

    def test_stub_with_empty_planner(self, sample_trip, mock_gemini_unavailable):
        agent = SchedulerAgent(gemini_client=mock_gemini_unavailable)
        result = agent.run(
            trip=sample_trip,
            planner_output={"days": []},
            weather_summary="N/A"
        )
        assert result.data["days"] == []

    def test_stub_uses_must_do_items(self, sample_trip, sample_planner_output, mock_gemini_unavailable):
        agent = SchedulerAgent(gemini_client=mock_gemini_unavailable)
        result = agent.run(
            trip=sample_trip,
            planner_output=sample_planner_output,
            weather_summary="Sunny"
        )

        # First block title should come from must_do
        first_block = result.data["days"][0]["schedule"][0]
        assert first_block["title"] == sample_planner_output["days"][0]["must_do"][0]
