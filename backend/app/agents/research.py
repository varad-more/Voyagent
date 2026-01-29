from __future__ import annotations

import json
import structlog
from app.core.gemini import GeminiClient
from app.services.places import get_hotels
from app.services.travel_time import get_travel_time_minutes
from app.utils.json_repair import best_effort_json

logger = structlog.get_logger(__name__)

class ResearchAgent:
    def __init__(self, gemini: GeminiClient):
        self.gemini = gemini

    async def conduct_research(self, request, session) -> str:
        """
        Conducts research on accommodation, transport, and local tips.
        Returns a formatted markdown string to be injected into the main prompt.
        """
        logger.info("research_agent_start", destination=request.destination)
        
        # 1. Accommodation Research
        comfort = request.budget.comfort_level or "moderate"
        hotels_payload = await get_hotels(
            destination=request.destination,
            comfort_level=comfort,
            session=session
        )
        hotels = hotels_payload.get("hotels", [])
        
        # Get alternative (cheaper) options if not already budget
        cheaper_hotels = []
        if comfort != "budget":
            cheaper_payload = await get_hotels(
                destination=request.destination,
                comfort_level="budget",
                session=session
            )
            cheaper_hotels = cheaper_payload.get("hotels", [])

        # 2. Commute/Transport Research
        # We check distance from origin if provided, else assume local travel within city
        transport_note = "Focus on local transit options."
        if request.origin_location:
            travel_time = await get_travel_time_minutes(
                origin=request.origin_location, 
                destination=request.destination, 
                session=session
            )
            mins = travel_time.get("travel_time_minutes", 0)
            hours = getattr(mins, 'real', mins) / 60
            transport_note = f"Travel from {request.origin_location} takes approx {hours:.1f} hours by car."

        # Format Research for LLM
        research_context = f"""
## Research Agent Report

### 🏨 Accommodation Options
**Primary ({comfort}):**
{self._format_hotels(hotels)}

**Cheaper Alternatives (Budget):**
{self._format_hotels(cheaper_hotels[:3])}

### 🚗 Transport & Commute
{transport_note}

### 💡 Local Commute Analysis (Gemini Analysis Required)
Please analyze the best way to get around {request.destination} (e.g., Rental Car vs Uber vs Public Transit) based on the activities chosen.
"""
        return research_context

    def _format_hotels(self, hotels: list[dict]) -> str:
        if not hotels:
            return "No data available."
        return "\n".join([f"- {h['name']} ({h.get('rating', 'N/A')}⭐) - {h['address']}" for h in hotels])

    async def get_travel_options(self, request, session) -> dict:
        """
        Uses Gemini to generate travel options for cars, hotels, flights AND a transport analysis.
        Returns a dict with 'booking_options' and 'transport_analysis'.
        """
        if not self.gemini:
            return self._get_stub_travel_options(request)

        # Get real hotel data for context
        comfort = request.budget.comfort_level or "moderate"
        hotels_payload = await get_hotels(
            destination=request.destination,
            comfort_level=comfort,
            session=session
        )
        hotels = hotels_payload.get("hotels", [])

        prompt = f"""
You are a travel booking assistant. Generate realistic travel options and a transport mode analysis for this trip:

Destination: {request.destination}
Origin: {request.origin_location or "Not specified"}
Dates: {request.start_date} to {request.end_date}
Travelers: {request.travelers.adults} adults, {request.travelers.children} children
Budget Level: {request.budget.comfort_level}
Total Budget: {request.budget.total_budget} {request.budget.currency}

Real Hotel Data Available:
{json.dumps(hotels[:3], default=str)}

Generate a JSON response with two keys:
1. "booking_options": 6 specific options (2 cars, 2 hotels, 2 flights) for booking.
2. "transport_analysis": Compare public vs private transport for getting around the destination.

JSON Format:
{{
  "booking_options": [
    {{
      "type": "car",
      "name": "Economy Sedan",
      "provider": "Enterprise",
      "price_estimate": "$45/day",
      "details": "Compact car, unlimited miles",
      "rating": 4.2,
      "features": ["GPS included", "Free cancellation"]
    }}
  ],
    "transport_analysis": {{
      "options": [
         {{
            "mode": "public_transit", 
            "description": "Bus and Metro system",
            "cost_estimate": "$5-10/day",
            "duration_estimate": "Wait times 5-10 mins",
            "fuel_cost_estimate": null,
            "misc_costs": ["Day Pass $5"],
            "pros": ["Cheap", "Eco-friendly"],
            "cons": ["Crowded"]
         }},
         {{
            "mode": "rental_car", 
            "description": "Self-drive rental",
            "cost_estimate": "$50/day + gas",
            "duration_estimate": "Flexible",
            "fuel_cost_estimate": "$15/day",
            "misc_costs": ["Parking ($20/day)", "Tolls"],
            "pros": ["Freedom", "Comfort"],
            "cons": ["Parking costs", "Traffic"]
         }}
      ],
      "recommended_mode": "public_transit",
      "reasoning": "Since you are staying downtown, public transit is faster and cheaper than parking."
  }}
}}

Return ONLY valid JSON.
"""
        try:
            raw = self.gemini.generate_content(prompt)
            data = best_effort_json(raw)
            # Validation
            if "booking_options" not in data:
                data["booking_options"] = []
            if "transport_analysis" not in data:
                data["transport_analysis"] = None
                
            logger.info("travel_options_generated", count=len(data["booking_options"]))
            return data
        except Exception as e:
            logger.warning("travel_options_generation_failed", error=str(e))
            return self._get_stub_travel_options(request)

    def _get_stub_travel_options(self, request) -> dict:
        """Fallback stub data for travel options."""
        return {
            "booking_options": [
                {
                    "type": "car",
                    "name": "Economy Sedan",
                    "provider": "Enterprise",
                    "price_estimate": "$40/day",
                    "details": f"Compact car for exploring {request.destination}",
                    "rating": 4.2,
                    "features": ["Unlimited miles", "Free cancellation"]
                },
                {
                    "type": "hotel",
                    "name": f"{request.destination} Central Hotel",
                    "provider": "Booking.com",
                    "price_estimate": "$120/night",
                    "details": "3-star hotel in city center",
                    "rating": 4.1,
                    "features": ["Free WiFi", "Breakfast included"]
                },
                {
                    "type": "flight",
                    "name": "Economy Class",
                    "provider": "United Airlines",
                    "price_estimate": "$300 round-trip",
                    "details": "Most affordable option",
                    "rating": 3.9,
                    "features": ["Carry-on included"]
                }
            ],
            "transport_analysis": {
                "options": [
                    {
                        "mode": "public_transit",
                        "description": "Local bus and train network",
                        "cost_estimate": "$10/day",
                        "duration_estimate": "Frequent service",
                        "fuel_cost_estimate": None,
                        "misc_costs": ["Transit Card"],
                        "pros": ["Affordable", "No parking worries"],
                        "cons": ["Less flexible", "Walking required"]
                    },
                    {
                        "mode": "rental_car",
                        "description": "Renting a private vehicle",
                        "cost_estimate": "$60/day",
                        "duration_estimate": "Flexible schedule",
                        "fuel_cost_estimate": "$10-20/day",
                        "misc_costs": ["Parking fees", "Tolls"],
                        "pros": ["Go anywhere", "Privacy"],
                        "cons": ["Parking fees", "Navigation stress"]
                    }
                ],
                "recommended_mode": "public_transit",
                "reasoning": f"Public transport is likely the best option for exploring {request.destination} efficiently."
            }
        }
