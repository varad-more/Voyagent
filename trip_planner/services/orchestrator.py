"""
Itinerary Orchestrator - Coordinates all agents.
"""
import logging
from datetime import datetime, timezone

from trip_planner.agents import (
    PlannerAgent, ResearchAgent, WeatherAgent, AttractionsAgent,
    SchedulerAgent, FoodAgent, BudgetAgent, ValidatorAgent
)
from trip_planner.services.gemini import gemini_client
from trip_planner.models import AgentTrace

logger = logging.getLogger(__name__)


def _build_packing_list(weather_data: dict, trip: dict) -> list:
    """Build packing list based on weather."""
    packing = {"Comfortable shoes", "Water bottle", "Phone charger", "Travel docs"}
    
    for day in weather_data.get("daily", []):
        high = day.get("high_c", 20)
        low = day.get("low_c", 10)
        precip = day.get("precipitation_chance", 0)
        
        if high >= 28:
            packing.update({"Lightweight clothes", "Sunhat", "Sunscreen"})
        if low <= 8:
            packing.update({"Warm jacket", "Layers", "Beanie"})
        if precip >= 0.4:
            packing.update({"Rain jacket", "Umbrella"})
    
    return sorted(packing)


def _store_trace(itinerary, agent_name: str, step: str, input_data=None, output_data=None, issues=None):
    """Store agent trace."""
    AgentTrace.create_trace(itinerary, agent_name, step, input_data, output_data, issues)


def _persist_result(itinerary, agent_name: str, input_data: dict, output_data: dict, drafts: list, issues: list):
    """Persist all traces for an agent."""
    for i, draft in enumerate(drafts):
        _store_trace(itinerary, agent_name, f"draft_{i+1}", input_data, {"draft": draft})
    _store_trace(itinerary, agent_name, "final", input_data, output_data, "; ".join(issues) if issues else None)


def generate_itinerary(trip: dict, itinerary) -> dict:
    """Generate complete itinerary by orchestrating all agents."""
    logger.info(f"Starting generation for {trip.get('destination')}")
    
    client = gemini_client if gemini_client.is_available else None
    
    # Initialize agents
    planner = PlannerAgent(client)
    research = ResearchAgent(client)
    weather = WeatherAgent(client)
    attractions = AttractionsAgent(client)
    scheduler = SchedulerAgent(client)
    food = FoodAgent(client)
    budget = BudgetAgent(client)
    validator = ValidatorAgent()
    
    # 1. Research
    research_context = ""
    if client:
        research_context = research.conduct_research(trip)
        _store_trace(itinerary, "research", "final", {"trip": trip}, {"context": research_context})
    
    # 2. Planner
    planner_result = planner.run(trip=trip, research_context=research_context)
    _persist_result(itinerary, "planner", {"trip": trip}, planner_result.data, 
                    planner_result.drafts, planner_result.issues)
    
    # 3. Weather
    weather_result = weather.run(trip=trip)
    _persist_result(itinerary, "weather", {"trip": trip}, weather_result.data,
                    weather_result.drafts, weather_result.issues)
    
    # 4. Attractions
    attractions_result = attractions.run(trip=trip)
    _persist_result(itinerary, "attractions", {"trip": trip}, attractions_result.data,
                    attractions_result.drafts, attractions_result.issues)
    
    # 5. Scheduler
    weather_overview = weather_result.data.get("weather", {}).get("overview", "Weather unavailable")
    scheduler_result = scheduler.run(trip=trip, planner_output=planner_result.data, weather_summary=weather_overview)
    _persist_result(itinerary, "scheduler", {"trip": trip}, scheduler_result.data,
                    scheduler_result.drafts, scheduler_result.issues)
    
    # 6. Food
    food_result = food.run(trip=trip, scheduler_output=scheduler_result.data)
    _persist_result(itinerary, "food", {"trip": trip}, food_result.data,
                    food_result.drafts, food_result.issues)
    
    # 7. Budget
    budget_result = budget.run(trip=trip, scheduler_output=scheduler_result.data, food_output=food_result.data)
    _persist_result(itinerary, "budget", {"trip": trip}, budget_result.data,
                    budget_result.drafts, budget_result.issues)
    
    # 8. Validator
    validator_result = validator.run(trip=trip, scheduler_output=scheduler_result.data)
    _persist_result(itinerary, "validator", {"trip": trip}, validator_result.data,
                    validator_result.drafts, validator_result.issues)
    
    # 9. Travel options
    travel_data = research.get_travel_options(trip)
    
    # Build final response
    dest = trip.get("destination", "")
    weather_adjustments = weather_result.data.get("adjustments", [])
    
    # Merge schedule with meals
    meals_by_date = {d.get("date"): d.get("meals", []) for d in food_result.data.get("days", [])}
    
    days = []
    for day in scheduler_result.data.get("days", []):
        day_date = day.get("date")
        days.append({
            "date": day_date,
            "title": f"{dest} - Day",
            "weather_summary": day.get("weather_summary", ""),
            "contingencies": weather_adjustments,
            "schedule": day.get("schedule", []),
            "meals": meals_by_date.get(day_date, []),
            "notes": day.get("notes", [])
        })
    
    packing = _build_packing_list(weather_result.data.get("weather", {}), trip)
    
    travel_options = [
        {
            "type": opt.get("type", "hotel"),
            "name": opt.get("name", ""),
            "provider": opt.get("provider", ""),
            "price_estimate": opt.get("price_estimate", ""),
            "details": opt.get("details", ""),
            "booking_url": opt.get("booking_url"),
            "rating": opt.get("rating"),
            "features": opt.get("features", [])
        }
        for opt in travel_data.get("booking_options", [])
    ]
    
    response = {
        "itinerary_id": str(itinerary.id),
        "summary": planner_result.data.get("summary", f"Trip to {dest}"),
        "days": days,
        "weather": weather_result.data.get("weather", {}),
        "attractions": attractions_result.data.get("attractions", []),
        "packing_list": packing,
        "budget": budget_result.data.get("budget", {}),
        "validation": validator_result.data.get("validation", []),
        "warnings": validator_result.data.get("warnings", []),
        "travel_options": travel_options,
        "transport_analysis": travel_data.get("transport_analysis"),
        "generated_at": datetime.now(timezone.utc).isoformat()
    }
    
    logger.info(f"Generation complete for {dest}")
    return response
