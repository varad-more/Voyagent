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
                    "description": {"type": "string"},
                    "reason": {"type": "string"},
                    "score": {"type": "number"},
                    "categories": {"type": "array", "items": {"type": "string"}},
                    "unique_features": {"type": "string", "description": "Ideally highlight if hidden gem or unique"},
                    "limited_time_note": {"type": "string", "description": "If seasonal event or temporary exhibit"},
                    "website": {"type": "string", "description": "Official link or info page"}
                },
                "required": ["name", "reason"]
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
        
        system = """Rank attractions by fit for traveler interests.
        CRITICAL: Prioritize "unique" experiences, "hidden gems", and "limited-time" events/festivals happening during the trip dates.
        Provide a website or Google Maps link if possible for each top attraction.
        """
        user = (
            f"Destination: {dest}\n"
            f"Dates: {trip.get('start_date')} to {trip.get('end_date')}\n"
            f"Interests: {interests}\n"
            f"Google Places Data: {places_data}\n"
        )
        
        try:
            data, drafts, issues = generate_validated(self.gemini_client, system, user, SCHEMA)
            return AgentResult(data=data, drafts=drafts, issues=issues)
        except Exception as e:
            logger.error(f"AttractionsAgent failed: {e}")
            return self._stub_result({"attractions": places_data.get("attractions", [])})
