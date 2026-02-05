"""
Food Agent - Plans meals aligned with schedule.
"""
import logging
from .base import BaseAgent, AgentResult
from trip_planner.services.gemini import generate_validated

logger = logging.getLogger(__name__)

SCHEMA = {
    "type": "object",
    "properties": {
        "days": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "date": {"type": "string"},
                    "meals": {"type": "array"}
                }
            }
        }
    }
}


class FoodAgent(BaseAgent):
    name = "food"
    
    def run(self, trip: dict, scheduler_output: dict) -> AgentResult:
        dest = trip.get("destination", "")
        food_prefs = trip.get("food_preferences", {})
        dietary = food_prefs.get("dietary_restrictions", [])
        cuisines = food_prefs.get("cuisines", [])
        
        if not self.has_ai:
            return self._create_stub(trip, scheduler_output)
        
        system = "Create meal plans that align with the schedule and dietary needs."
        user = f"Destination: {dest}\nDietary: {dietary}\nCuisines: {cuisines}\nSchedule: {scheduler_output}"
        
        try:
            data, drafts, issues = generate_validated(self.gemini_client, system, user, SCHEMA)
            return AgentResult(data=data, drafts=drafts, issues=issues)
        except Exception as e:
            logger.error(f"FoodAgent failed: {e}")
            return self._create_stub(trip, scheduler_output)
    
    def _create_stub(self, trip: dict, scheduler: dict) -> AgentResult:
        dest = trip.get("destination", "")
        dietary = trip.get("food_preferences", {}).get("dietary_restrictions", [])
        
        days = []
        for day in scheduler.get("days", []):
            days.append({
                "date": day.get("date"),
                "meals": [
                    {"time": "08:30", "name": "Breakfast cafe", "cuisine": "Local",
                     "dietary_fit": dietary, "location": dest, "reservation_needed": False, "estimated_cost": 15},
                    {"time": "12:30", "name": "Lunch bistro", "cuisine": "Regional",
                     "dietary_fit": dietary, "location": dest, "reservation_needed": False, "estimated_cost": 25},
                    {"time": "19:00", "name": "Dinner spot", "cuisine": "Contemporary",
                     "dietary_fit": dietary, "location": dest, "reservation_needed": True, "estimated_cost": 45},
                ]
            })
        
        return self._stub_result({"days": days})
