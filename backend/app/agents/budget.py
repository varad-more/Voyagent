from __future__ import annotations

from app.agents.base import AgentResult, BaseAgent
from app.core.gemini import generate_validated
from app.schemas.agents import BudgetOutput
from app.schemas.itinerary import BudgetItem, BudgetPlan, TripRequest


class BudgetAgent(BaseAgent):
    name = "budget"

    async def run(self, *, trip: TripRequest, scheduler_output, food_output) -> AgentResult:
        if not self.gemini_client:
            breakdown = [
                BudgetItem(category="Lodging", estimated_cost=trip.budget.total_budget * 0.45),
                BudgetItem(category="Meals", estimated_cost=trip.budget.total_budget * 0.2),
                BudgetItem(category="Activities", estimated_cost=trip.budget.total_budget * 0.2),
                BudgetItem(category="Transit", estimated_cost=trip.budget.total_budget * 0.1),
                BudgetItem(category="Buffer", estimated_cost=trip.budget.total_budget * 0.05),
            ]
            estimated_total = sum(item.estimated_cost for item in breakdown)
            warnings = []
            downgrade_plan = []
            if estimated_total > trip.budget.total_budget:
                warnings.append("Estimated total exceeds budget.")
                downgrade_plan = [
                    "Swap one paid attraction for a free walking tour.",
                    "Choose mid-range dining for two dinners.",
                    "Use public transit for intra-city travel.",
                ]
            output = BudgetOutput(
                budget=BudgetPlan(
                    currency=trip.budget.currency,
                    total_budget=trip.budget.total_budget,
                    estimated_total=estimated_total,
                    breakdown=breakdown,
                    warnings=warnings,
                    downgrade_plan=downgrade_plan,
                )
            )
            return AgentResult(data=output, drafts=[], issues=["gemini_disabled"])

        system = (
            "You are a travel budget analyst. Build a cost breakdown and a downgrade"
            " plan if over budget."
        )
        user = (
            f"Budget: {trip.budget.model_dump()}\n"
            f"Schedule: {scheduler_output.model_dump()}\n"
            f"Meals: {food_output.model_dump()}"
        )
        data, drafts, issues = generate_validated(
            client=self.gemini_client,
            system_prompt=system,
            user_prompt=user,
            model_cls=BudgetOutput,
        )
        return AgentResult(data=data, drafts=drafts, issues=issues)
