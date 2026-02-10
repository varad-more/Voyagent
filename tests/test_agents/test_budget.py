"""
Tests for the BudgetAgent.
"""
import pytest

from trip_planner.agents.budget import BudgetAgent


class TestBudgetAgentStub:
    def test_stub_output_structure(self, sample_trip, sample_scheduler_output, sample_food_output,
                                    mock_gemini_unavailable):
        agent = BudgetAgent(gemini_client=mock_gemini_unavailable)
        result = agent.run(
            trip=sample_trip,
            scheduler_output=sample_scheduler_output,
            food_output=sample_food_output,
        )

        assert result.data is not None
        assert "budget" in result.data
        budget = result.data["budget"]
        assert "currency" in budget
        assert "total_budget" in budget
        assert "estimated_total" in budget
        assert "breakdown" in budget
        assert "warnings" in budget
        assert "downgrade_plan" in budget

    def test_stub_breakdown_categories(self, sample_trip, sample_scheduler_output, sample_food_output,
                                       mock_gemini_unavailable):
        agent = BudgetAgent(gemini_client=mock_gemini_unavailable)
        result = agent.run(trip=sample_trip, scheduler_output=sample_scheduler_output,
                          food_output=sample_food_output)

        categories = [b["category"] for b in result.data["budget"]["breakdown"]]
        assert "Lodging" in categories
        assert "Meals" in categories
        assert "Activities" in categories

    def test_stub_uses_trip_currency(self, sample_trip, sample_scheduler_output, sample_food_output,
                                    mock_gemini_unavailable):
        agent = BudgetAgent(gemini_client=mock_gemini_unavailable)
        result = agent.run(trip=sample_trip, scheduler_output=sample_scheduler_output,
                          food_output=sample_food_output)
        assert result.data["budget"]["currency"] == "EUR"

    def test_stub_uses_trip_total_budget(self, sample_trip, sample_scheduler_output, sample_food_output,
                                        mock_gemini_unavailable):
        agent = BudgetAgent(gemini_client=mock_gemini_unavailable)
        result = agent.run(trip=sample_trip, scheduler_output=sample_scheduler_output,
                          food_output=sample_food_output)
        assert result.data["budget"]["total_budget"] == 2000.0

    def test_stub_no_warnings_within_budget(self, sample_trip, sample_scheduler_output, sample_food_output,
                                            mock_gemini_unavailable):
        agent = BudgetAgent(gemini_client=mock_gemini_unavailable)
        result = agent.run(trip=sample_trip, scheduler_output=sample_scheduler_output,
                          food_output=sample_food_output)
        budget = result.data["budget"]
        # Estimated should equal the budget (all percentages sum to 1.0)
        assert budget["estimated_total"] <= budget["total_budget"]

    def test_stub_default_budget(self, mock_gemini_unavailable):
        """When no budget specified, default of 1000 is used."""
        trip = {"budget": {}}
        agent = BudgetAgent(gemini_client=mock_gemini_unavailable)
        result = agent.run(trip=trip, scheduler_output={"days": [{"date": "2026-04-01"}]},
                          food_output={"days": []})
        assert result.data["budget"]["total_budget"] == 1000
