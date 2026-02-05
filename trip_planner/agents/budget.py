"""
Budget Agent - Calculates costs and suggests optimizations.
"""
import logging
from .base import BaseAgent, AgentResult
from trip_planner.services.gemini import generate_validated

logger = logging.getLogger(__name__)

SCHEMA = {
    "type": "object",
    "properties": {
        "budget": {
            "type": "object",
            "properties": {
                "currency": {"type": "string"},
                "total_budget": {"type": "number"},
                "estimated_total": {"type": "number"},
                "breakdown": {"type": "array"},
                "warnings": {"type": "array", "items": {"type": "string"}},
                "downgrade_plan": {"type": "array", "items": {"type": "string"}}
            }
        }
    }
}


class BudgetAgent(BaseAgent):
    name = "budget"
    
    def run(self, trip: dict, scheduler_output: dict, food_output: dict) -> AgentResult:
        budget_info = trip.get("budget", {})
        
        if not self.has_ai:
            return self._create_stub(trip, scheduler_output, food_output)
        
        system = "Calculate budget breakdown with warnings and downgrade suggestions if over budget."
        user = f"Budget: {budget_info}\nSchedule: {scheduler_output}\nMeals: {food_output}"
        
        try:
            data, drafts, issues = generate_validated(self.gemini_client, system, user, SCHEMA)
            return AgentResult(data=data, drafts=drafts, issues=issues)
        except Exception as e:
            logger.error(f"BudgetAgent failed: {e}")
            return self._create_stub(trip, scheduler_output, food_output)
    
    def _create_stub(self, trip: dict, scheduler: dict, food: dict) -> AgentResult:
        budget_info = trip.get("budget", {})
        total = budget_info.get("total_budget", 1000)
        currency = budget_info.get("currency", "USD")
        num_days = max(1, len(scheduler.get("days", [])))
        
        breakdown = [
            {"category": "Lodging", "estimated_cost": round(total * 0.40, 2)},
            {"category": "Meals", "estimated_cost": round(total * 0.25, 2)},
            {"category": "Activities", "estimated_cost": round(total * 0.20, 2)},
            {"category": "Transit", "estimated_cost": round(total * 0.10, 2)},
            {"category": "Buffer", "estimated_cost": round(total * 0.05, 2)},
        ]
        
        estimated = sum(b["estimated_cost"] for b in breakdown)
        warnings = []
        downgrade = []
        
        if estimated > total:
            warnings.append(f"Estimated {currency} {estimated:.0f} exceeds budget.")
            downgrade = [
                "Swap paid attractions for free tours.",
                "Choose budget dining options.",
                "Use public transit.",
            ]
        
        return self._stub_result({
            "budget": {
                "currency": currency,
                "total_budget": total,
                "estimated_total": estimated,
                "breakdown": breakdown,
                "warnings": warnings,
                "downgrade_plan": downgrade
            }
        })
