"""
Attractions Agent - Finds and ranks attractions.
"""
import logging
from .base import BaseAgent, AgentResult
from trip_planner.services.places import get_attractions
from trip_planner.services.gemini import generate_validated

logger = logging.getLogger(__name__)

SCHEMA = {
    "type": "object",
    "properties": {
        "attractions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "reason": {"type": "string"},
                    "score": {"type": "number"},
                    "categories": {"type": "array", "items": {"type": "string"}}
                }
            }
        }
    }
}


class AttractionsAgent(BaseAgent):
    name = "attractions"
    
    def run(self, trip: dict) -> AgentResult:
        dest = trip.get("destination", "")
        interests = trip.get("activity_preferences", {}).get("interests", [])
        
        places_data = get_attractions(dest, interests)
        
        if not self.has_ai:
            return self._stub_result({"attractions": places_data.get("attractions", [])})
        
        system = "Rank attractions by fit for traveler interests."
        user = f"Destination: {dest}\nInterests: {interests}\nPlaces: {places_data}"
        
        try:
            data, drafts, issues = generate_validated(self.gemini_client, system, user, SCHEMA)
            return AgentResult(data=data, drafts=drafts, issues=issues)
        except Exception as e:
            logger.error(f"AttractionsAgent failed: {e}")
            return self._stub_result({"attractions": places_data.get("attractions", [])})
