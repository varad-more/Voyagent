"""
Weather Agent - Fetches and analyzes weather.
"""
import logging
from datetime import date
from .base import BaseAgent, AgentResult
from trip_planner.services.weather import get_weather
from trip_planner.services.gemini import generate_validated

logger = logging.getLogger(__name__)

SCHEMA = {
    "type": "object",
    "properties": {
        "weather": {"type": "object"},
        "adjustments": {"type": "array", "items": {"type": "string"}}
    }
}


class WeatherAgent(BaseAgent):
    name = "weather"
    
    def run(self, trip: dict) -> AgentResult:
        dest = trip.get("destination", "")
        start = trip.get("start_date")
        end = trip.get("end_date")
        
        if isinstance(start, str):
            start = date.fromisoformat(start)
        if isinstance(end, str):
            end = date.fromisoformat(end)
        
        weather_data = get_weather(dest, start, end)
        
        if not self.has_ai:
            adjustments = ["Pack a light rain jacket."]
            for day in weather_data.get("daily", []):
                if day.get("precipitation_chance", 0) > 0.5:
                    adjustments.append("High rain chance - have indoor backups.")
                    break
            return self._stub_result({"weather": weather_data, "adjustments": adjustments})
        
        system = "Analyze weather and suggest schedule adjustments."
        user = f"Destination: {dest}\nForecast: {weather_data}"
        
        try:
            data, drafts, issues = generate_validated(self.gemini_client, system, user, SCHEMA)
            return AgentResult(data=data, drafts=drafts, issues=issues)
        except Exception as e:
            logger.error(f"WeatherAgent failed: {e}")
            return self._stub_result({"weather": weather_data, "adjustments": ["Pack layers."]})
