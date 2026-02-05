"""
Scheduler Agent - Converts plans to timed schedules.
"""
import logging
from django.conf import settings
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
                    "weather_summary": {"type": "string"},
                    "schedule": {"type": "array"},
                    "notes": {"type": "array", "items": {"type": "string"}}
                }
            }
        }
    }
}


class SchedulerAgent(BaseAgent):
    name = "scheduler"
    
    def run(self, trip: dict, planner_output: dict, weather_summary: str) -> AgentResult:
        dest = trip.get("destination", "")
        
        if not self.has_ai:
            return self._create_stub(trip, planner_output, weather_summary)
        
        buffer = settings.PLANNER_BUFFER_MINUTES
        system = "Convert skeleton plan to timed schedule with realistic travel/buffer times."
        user = (
            f"Destination: {dest}\n"
            f"Daily window: {trip.get('daily_start_time', '09:00')} - {trip.get('daily_end_time', '20:00')}\n"
            f"Buffer: {buffer} mins\nWeather: {weather_summary}\n"
            f"Plan: {planner_output}"
        )
        
        try:
            data, drafts, issues = generate_validated(self.gemini_client, system, user, SCHEMA)
            return AgentResult(data=data, drafts=drafts, issues=issues)
        except Exception as e:
            logger.error(f"SchedulerAgent failed: {e}")
            return self._create_stub(trip, planner_output, weather_summary)
    
    def _create_stub(self, trip: dict, planner: dict, weather: str) -> AgentResult:
        dest = trip.get("destination", "")
        days = []
        
        for day in planner.get("days", []):
            must_do = day.get("must_do", ["Activity"])
            optional = day.get("optional_stops", ["Explore"])
            
            schedule = [
                {"start_time": "09:00", "end_time": "11:30", "title": must_do[0] if must_do else "Morning",
                 "location": dest, "description": "Main activity", "block_type": "activity",
                 "travel_time_mins": 20, "buffer_mins": 15, "micro_activities": []},
                {"start_time": "12:00", "end_time": "13:30", "title": "Lunch",
                 "location": dest, "description": "Local dining", "block_type": "meal",
                 "travel_time_mins": 10, "buffer_mins": 10, "micro_activities": []},
                {"start_time": "14:00", "end_time": "17:30", "title": optional[0] if optional else "Afternoon",
                 "location": dest, "description": "Exploration", "block_type": "activity",
                 "travel_time_mins": 20, "buffer_mins": 20, "micro_activities": []},
            ]
            
            days.append({
                "date": day.get("date"),
                "weather_summary": weather,
                "schedule": schedule,
                "notes": [f"Theme: {day.get('theme', 'Explore')}"]
            })
        
        return self._stub_result({"days": days})
