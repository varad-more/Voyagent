"""
Shared test fixtures for the Trip Planner test suite.
"""
import json
import pytest
from datetime import date, time, timedelta
from unittest.mock import MagicMock, PropertyMock


# ---------------------------------------------------------------------------
# Trip request fixtures
# ---------------------------------------------------------------------------

def _future_date(days_ahead: int) -> str:
    """Return an ISO date string N days in the future."""
    return (date.today() + timedelta(days=days_ahead)).isoformat()


@pytest.fixture
def sample_trip():
    """Standard 3-day trip to Paris."""
    return {
        "destination": "Paris, France",
        "start_date": _future_date(30),
        "end_date": _future_date(32),
        "travelers": {"adults": 2, "children": 0},
        "origin_location": "London, UK",
        "food_preferences": {
            "cuisines": ["french", "italian"],
            "dietary_restrictions": ["vegetarian"],
            "avoid_ingredients": [],
        },
        "activity_preferences": {
            "interests": ["museums", "history", "food"],
            "pace": "moderate",
            "accessibility_needs": [],
        },
        "lodging_preferences": {
            "lodging_type": "hotel",
            "max_distance_km_from_center": 3.0,
        },
        "budget": {
            "currency": "EUR",
            "total_budget": 2000.0,
            "comfort_level": "midrange",
        },
        "daily_start_time": "09:00",
        "daily_end_time": "20:00",
        "notes": "First time visiting Paris",
    }


@pytest.fixture
def unknown_location_trip():
    """Trip to an obscure location — Faroe Islands."""
    return {
        "destination": "Tórshavn, Faroe Islands",
        "start_date": _future_date(60),
        "end_date": _future_date(63),
        "travelers": {"adults": 1, "children": 0},
        "food_preferences": {"cuisines": [], "dietary_restrictions": [], "avoid_ingredients": []},
        "activity_preferences": {"interests": ["hiking", "nature"], "pace": "slow", "accessibility_needs": []},
        "lodging_preferences": {"lodging_type": "any", "max_distance_km_from_center": 5.0},
        "budget": {"currency": "DKK", "total_budget": 15000.0, "comfort_level": "midrange"},
        "daily_start_time": "08:00",
        "daily_end_time": "21:00",
    }


@pytest.fixture
def multi_city_trip():
    """Multi-city road trip."""
    return {
        "destination": "Tempe -> Grand Canyon -> Las Vegas",
        "start_date": _future_date(45),
        "end_date": _future_date(49),
        "travelers": {"adults": 2, "children": 1},
        "origin_location": "Phoenix, AZ",
        "food_preferences": {"cuisines": ["american", "mexican"], "dietary_restrictions": [], "avoid_ingredients": []},
        "activity_preferences": {"interests": ["nature", "sightseeing"], "pace": "moderate", "accessibility_needs": []},
        "lodging_preferences": {"lodging_type": "hotel", "max_distance_km_from_center": 5.0},
        "budget": {"currency": "USD", "total_budget": 3000.0, "comfort_level": "midrange"},
        "daily_start_time": "07:00",
        "daily_end_time": "22:00",
    }


# ---------------------------------------------------------------------------
# Mock Gemini client
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_gemini_client():
    """A mock GeminiClient that returns plausible JSON responses."""
    client = MagicMock()
    type(client).is_available = PropertyMock(return_value=True)

    def mock_generate(prompt, schema=None):
        """Return a plausible JSON string based on prompt content."""
        prompt_lower = prompt.lower() if isinstance(prompt, str) else ""

        if "skeleton plan" in prompt_lower or "planner" in prompt_lower:
            return json.dumps({
                "summary": "A wonderful trip",
                "days": [
                    {"date": _future_date(30), "theme": "Exploration",
                     "must_do": ["Visit landmark", "Walk the streets"],
                     "optional_stops": ["Cafe", "Park"]}
                ]
            })
        elif "weather" in prompt_lower or "forecast" in prompt_lower:
            return json.dumps({
                "weather": {"overview": "Mild and sunny", "daily": []},
                "adjustments": ["Pack sunscreen"]
            })
        elif "attraction" in prompt_lower or "rank" in prompt_lower:
            return json.dumps({
                "attractions": [
                    {"name": "Famous Place", "reason": "Historic", "score": 0.9, "categories": ["landmark"]}
                ]
            })
        elif "schedule" in prompt_lower or "timed" in prompt_lower:
            return json.dumps({
                "days": [{
                    "date": _future_date(30),
                    "weather_summary": "Sunny",
                    "schedule": [
                        {"start_time": "09:00", "end_time": "11:30", "title": "Morning Activity",
                         "location": "City Center", "description": "Explore", "block_type": "activity",
                         "travel_time_mins": 15, "buffer_mins": 10, "micro_activities": []}
                    ],
                    "notes": ["Have fun!"]
                }]
            })
        elif "meal" in prompt_lower or "food" in prompt_lower:
            return json.dumps({
                "days": [{
                    "date": _future_date(30),
                    "meals": [
                        {"time": "12:00", "name": "Local Bistro", "cuisine": "French",
                         "dietary_fit": [], "location": "Downtown", "reservation_needed": False,
                         "estimated_cost": 25}
                    ]
                }]
            })
        elif "budget" in prompt_lower or "cost" in prompt_lower:
            return json.dumps({
                "budget": {
                    "currency": "USD", "total_budget": 2000, "estimated_total": 1500,
                    "breakdown": [{"category": "Lodging", "estimated_cost": 600}],
                    "warnings": [], "downgrade_plan": []
                }
            })
        elif "booking" in prompt_lower or "travel option" in prompt_lower:
            return json.dumps({
                "booking_options": [
                    {"type": "hotel", "name": "City Hotel", "provider": "Booking.com",
                     "price_estimate": "$120/night", "details": "3-star", "rating": 4.0, "features": ["WiFi"]}
                ],
                "transport_analysis": {
                    "options": [{"mode": "public_transit", "description": "Metro", "cost_estimate": "$5/day",
                                 "pros": ["Cheap"], "cons": ["Crowded"]}],
                    "recommended_mode": "public_transit",
                    "reasoning": "Best value."
                }
            })
        elif "edit" in prompt_lower:
            return json.dumps({
                "start_time": "10:00", "end_time": "12:00", "title": "Edited Activity",
                "location": "New Place", "description": "Updated", "block_type": "activity",
                "travel_time_mins": 10, "buffer_mins": 5, "micro_activities": []
            })
        else:
            return json.dumps({"result": "ok"})

    client.generate_content = MagicMock(side_effect=mock_generate)
    return client


@pytest.fixture
def mock_gemini_unavailable():
    """A GeminiClient that is not available (no API key)."""
    client = MagicMock()
    type(client).is_available = PropertyMock(return_value=False)
    client._error_reason = "Gemini API key not configured"
    return client


# ---------------------------------------------------------------------------
# Planner output fixtures (for agents that depend on earlier stages)
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_planner_output():
    """Output from PlannerAgent for use by downstream agents."""
    return {
        "summary": "3 days in Paris",
        "days": [
            {"date": _future_date(30), "theme": "History", "must_do": ["Eiffel Tower"], "optional_stops": ["Cafe"]},
            {"date": _future_date(31), "theme": "Art", "must_do": ["Louvre"], "optional_stops": ["Luxembourg"]},
            {"date": _future_date(32), "theme": "Local Life", "must_do": ["Montmartre"], "optional_stops": ["Market"]},
        ]
    }


@pytest.fixture
def sample_scheduler_output():
    """Output from SchedulerAgent for use by downstream agents."""
    return {
        "days": [
            {
                "date": _future_date(30),
                "weather_summary": "Sunny, 22°C",
                "schedule": [
                    {"start_time": "09:00", "end_time": "11:30", "title": "Eiffel Tower",
                     "location": "Champ de Mars", "description": "Visit", "block_type": "activity",
                     "travel_time_mins": 20, "buffer_mins": 15, "micro_activities": []},
                    {"start_time": "12:00", "end_time": "13:30", "title": "Lunch",
                     "location": "Le Marais", "description": "French cuisine", "block_type": "meal",
                     "travel_time_mins": 15, "buffer_mins": 10, "micro_activities": []},
                    {"start_time": "14:00", "end_time": "17:00", "title": "Seine Cruise",
                     "location": "Seine River", "description": "Boat tour", "block_type": "activity",
                     "travel_time_mins": 10, "buffer_mins": 15, "micro_activities": []},
                ],
                "notes": ["Book Eiffel Tower tickets online"]
            }
        ]
    }


@pytest.fixture
def sample_food_output():
    """Output from FoodAgent for use by downstream agents."""
    return {
        "days": [
            {
                "date": _future_date(30),
                "meals": [
                    {"time": "08:30", "name": "Boulangerie", "cuisine": "French",
                     "dietary_fit": ["vegetarian"], "location": "Paris", "reservation_needed": False,
                     "estimated_cost": 12},
                    {"time": "12:30", "name": "Bistro Parisien", "cuisine": "French",
                     "dietary_fit": ["vegetarian"], "location": "Le Marais", "reservation_needed": False,
                     "estimated_cost": 30},
                    {"time": "19:00", "name": "Le Comptoir", "cuisine": "French",
                     "dietary_fit": ["vegetarian"], "location": "Saint-Germain", "reservation_needed": True,
                     "estimated_cost": 55},
                ]
            }
        ]
    }
