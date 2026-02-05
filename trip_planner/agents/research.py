"""
Research Agent - Researches accommodation and transport.
"""
import json
import logging
from trip_planner.services.places import get_hotels
from trip_planner.services.travel_time import get_travel_time_minutes
from trip_planner.core.utils import best_effort_json

logger = logging.getLogger(__name__)


class ResearchAgent:
    """Conducts research on accommodation and transport."""
    name = "research"
    
    def __init__(self, gemini_client=None):
        self.gemini = gemini_client
    
    @property
    def has_ai(self) -> bool:
        return self.gemini is not None and self.gemini.is_available
    
    def conduct_research(self, request: dict) -> str:
        """Research accommodation and transport, return markdown context."""
        dest = request.get("destination", "")
        comfort = request.get("budget", {}).get("comfort_level", "midrange")
        
        hotels = get_hotels(dest, comfort).get("hotels", [])
        budget_hotels = get_hotels(dest, "budget").get("hotels", []) if comfort != "budget" else []
        
        transport_note = "Focus on local transit."
        if request.get("origin_location"):
            travel = get_travel_time_minutes(request["origin_location"], dest)
            hours = travel.get("travel_time_minutes", 0) / 60
            transport_note = f"Travel from {request['origin_location']}: ~{hours:.1f}h by car."
        
        hotel_fmt = lambda h: f"- {h['name']} ({h.get('rating', 'N/A')}★)"
        
        return f"""
## Research Report

### Accommodation ({comfort})
{chr(10).join(hotel_fmt(h) for h in hotels[:3]) or 'No data'}

### Budget Alternatives
{chr(10).join(hotel_fmt(h) for h in budget_hotels[:2]) or 'N/A'}

### Transport
{transport_note}
"""
    
    def get_travel_options(self, request: dict) -> dict:
        """Generate travel options and transport analysis."""
        if not self.has_ai:
            return self._stub_options(request)
        
        dest = request.get("destination", "")
        comfort = request.get("budget", {}).get("comfort_level", "midrange")
        hotels = get_hotels(dest, comfort).get("hotels", [])
        
        prompt = f"""
Generate travel booking options for:
Destination: {dest}
Dates: {request.get('start_date')} to {request.get('end_date')}
Budget: {request.get('budget', {}).get('comfort_level', 'midrange')}

Hotels available: {json.dumps(hotels[:3], default=str)}

Return JSON with:
- "booking_options": array of {{type, name, provider, price_estimate, details, rating, features}}
- "transport_analysis": {{options: [{{mode, description, cost_estimate, pros, cons}}], recommended_mode, reasoning}}
"""
        try:
            raw = self.gemini.generate_content(prompt)
            data = best_effort_json(raw)
            data.setdefault("booking_options", [])
            data.setdefault("transport_analysis", None)
            return data
        except Exception as e:
            logger.warning(f"Travel options failed: {e}")
            return self._stub_options(request)
    
    def _stub_options(self, request: dict) -> dict:
        dest = request.get("destination", "destination")
        return {
            "booking_options": [
                {"type": "car", "name": "Economy Sedan", "provider": "Enterprise", 
                 "price_estimate": "$40/day", "details": "Compact car", "rating": 4.2, "features": ["Unlimited miles"]},
                {"type": "hotel", "name": f"{dest} Central Hotel", "provider": "Booking.com",
                 "price_estimate": "$120/night", "details": "3-star", "rating": 4.1, "features": ["WiFi", "Breakfast"]},
                {"type": "flight", "name": "Economy", "provider": "United", 
                 "price_estimate": "$300 RT", "details": "Standard", "rating": 3.9, "features": ["Carry-on"]},
            ],
            "transport_analysis": {
                "options": [
                    {"mode": "public_transit", "description": "Local buses/trains", "cost_estimate": "$10/day",
                     "pros": ["Affordable"], "cons": ["Less flexible"]},
                    {"mode": "rental_car", "description": "Self-drive", "cost_estimate": "$60/day",
                     "pros": ["Freedom"], "cons": ["Parking costs"]},
                ],
                "recommended_mode": "public_transit",
                "reasoning": "Cost-effective for city exploration."
            }
        }
