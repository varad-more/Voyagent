"""
Planner Agent - Creates day-by-day skeleton plans.
"""
import logging
from datetime import date, timedelta
from .base import BaseAgent, AgentResult
from trip_planner.services.gemini import generate_validated

logger = logging.getLogger(__name__)

SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "days": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "date": {"type": "string"},
                    "theme": {"type": "string"},
                    "must_do": {"type": "array", "items": {"type": "string"}},
                    "optional_stops": {"type": "array", "items": {"type": "string"}}
                }
            }
        }
    }
}


class PlannerAgent(BaseAgent):
    name = "planner"
    
    def run(self, trip: dict, research_context: str = None) -> AgentResult:
        logger.info(f"PlannerAgent: {trip.get('destination')}")
        
        if not self.has_ai:
            return self._create_stub(trip)
        
        interests = trip.get("activity_preferences", {}).get("interests", [])
        travelers = trip.get("travelers", {})
        
        system = "You are a travel planner. Create a day-by-day skeleton plan with must-do and optional stops."
        user = (
            f"Destination: {trip.get('destination')}\n"
            f"Dates: {trip.get('start_date')} to {trip.get('end_date')}\n"
            f"Travelers: {travelers.get('adults', 1)} adults, {travelers.get('children', 0)} children\n"
            f"Interests: {', '.join(interests) or 'General'}\n"
            f"Pace: {trip.get('activity_preferences', {}).get('pace', 'moderate')}\n"
        )
        if research_context:
            user += f"\nResearch:\n{research_context}"
        
        try:
            data, drafts, issues = generate_validated(self.gemini_client, system, user, SCHEMA)
            return AgentResult(data=data, drafts=drafts, issues=issues)
        except Exception as e:
            logger.error(f"PlannerAgent failed: {e}")
            return self._create_stub(trip)
    
    def _create_stub(self, trip: dict) -> AgentResult:
        start = trip.get("start_date")
        end = trip.get("end_date")
        dest = trip.get("destination", "destination")
        
        if isinstance(start, str):
            start = date.fromisoformat(start)
        if isinstance(end, str):
            end = date.fromisoformat(end)
        
        days = []
        current = start
        while current <= end:
            days.append({
                "date": current.isoformat(),
                "theme": "Exploration day",
                "must_do": ["Main attraction", "Local walk"],
                "optional_stops": ["Cafe", "Viewpoint"]
            })
            current += timedelta(days=1)
        
        return self._stub_result({
            "summary": f"Trip to {dest}",
            "days": days
        })
