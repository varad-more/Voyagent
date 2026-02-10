"""
Itinerary Orchestrator - Coordinates all agents with parallel execution.

Pipeline stages (agents within a stage run concurrently):
  Stage 1: Research
  Stage 2: Planner
  Stage 3: Weather + Attractions   (parallel — both only need trip data)
  Stage 4: Scheduler
  Stage 5: Food + Validator        (parallel — independent after scheduler)
  Stage 6: Budget
"""
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from trip_planner.agents import (
    PlannerAgent, ResearchAgent, WeatherAgent, AttractionsAgent,
    SchedulerAgent, FoodAgent, BudgetAgent, ValidatorAgent
)
from trip_planner.agents.base import AgentResult
from trip_planner.services.gemini import gemini_client
from trip_planner.models import AgentTrace
from trip_planner.core.exceptions import GeminiError
from trip_planner.core.booking_links import generate_booking_links

logger = logging.getLogger(__name__)

# Max workers for parallel agent execution (2 is enough for our paired stages)
_PARALLEL_WORKERS = 2


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


def _mock_result(data: dict, error: str) -> AgentResult:
    """Create a mock AgentResult for failed agents."""
    return AgentResult(data=data, drafts=[], issues=[error])


def _run_agent_safe(agent_fn, agent_name: str, fallback_data: dict, itinerary, trip: dict):
    """Run an agent function safely, returning a mock result on failure."""
    try:
        result = agent_fn()
        _persist_result(itinerary, agent_name, {"trip": trip}, result.data,
                        result.drafts, result.issues)
        return result
    except Exception as e:
        logger.error(f"{agent_name} agent failed: {e}")
        _store_trace(itinerary, agent_name, "failed", {"trip": trip}, None, str(e))
        return _mock_result(fallback_data, str(e))


def generate_itinerary(trip: dict, itinerary, progress_cb=None) -> dict:
    """Generate complete itinerary by orchestrating all agents.

    Independent stages are executed in parallel using a thread pool,
    cutting total wall-clock time by ~30-40 %.

    Args:
        trip: Trip request data dict.
        itinerary: Itinerary model instance.
        progress_cb: Optional callback ``fn(stage_name, status, detail)``
                     called as each stage starts / finishes for SSE streaming.
    """
    def _progress(stage: str, status: str, detail: str = ""):
        if progress_cb:
            try:
                progress_cb(stage, status, detail)
            except Exception:
                pass  # never break the pipeline for a progress issue

    logger.info(f"Starting generation for {trip.get('destination')}")
    t_start = time.monotonic()
    
    client = gemini_client if gemini_client.is_available else None
    if not client:
        reason = getattr(gemini_client, "_error_reason", "Gemini API key not configured")
        raise GeminiError(reason)
    
    # Initialize agents
    planner = PlannerAgent(client)
    research = ResearchAgent(client)
    weather = WeatherAgent(client)
    attractions = AttractionsAgent(client)
    scheduler = SchedulerAgent(client)
    food = FoodAgent(client)
    budget = BudgetAgent(client)
    validator = ValidatorAgent()
    
    # ── Stage 1: Research (sequential) ──────────────────────────────
    _progress("research", "started", "Researching your destination...")
    research_context = ""
    if client:
        research_context = research.conduct_research(trip)
        _store_trace(itinerary, "research", "final", {"trip": trip}, {"context": research_context})
    _progress("research", "done")
    
    # ── Stage 2: Planner (sequential — needs research) ──────────────
    _progress("planner", "started", "Planning your days...")
    time.sleep(2)  # Rate limit buffer
    planner_result = planner.run(trip=trip, research_context=research_context)
    _persist_result(itinerary, "planner", {"trip": trip}, planner_result.data, 
                    planner_result.drafts, planner_result.issues)
    _progress("planner", "done")
    
    # ── Stage 3: Weather + Attractions (PARALLEL) ───────────────────
    _progress("weather_attractions", "started", "Checking weather & finding attractions...")
    time.sleep(2)  # Rate limit buffer before parallel burst
    with ThreadPoolExecutor(max_workers=_PARALLEL_WORKERS) as pool:
        weather_future = pool.submit(
            _run_agent_safe,
            lambda: weather.run(trip=trip),
            "weather",
            {"weather": {}, "adjustments": []},
            itinerary, trip
        )
        attractions_future = pool.submit(
            _run_agent_safe,
            lambda: attractions.run(trip=trip),
            "attractions",
            {"attractions": []},
            itinerary, trip
        )
        weather_result = weather_future.result()
        attractions_result = attractions_future.result()
    
    logger.info("Stage 3 complete (Weather + Attractions ran in parallel)")
    _progress("weather_attractions", "done")
    
    # ── Stage 4: Scheduler (sequential — needs planner + weather + attractions) ──
    _progress("scheduler", "started", "Building your schedule...")
    time.sleep(2)  # Rate limit buffer
    weather_overview = weather_result.data.get("weather", {}).get("overview", "Weather unavailable")
    scheduler_result = scheduler.run(
        trip=trip, 
        planner_output=planner_result.data, 
        weather_summary=weather_overview,
        attractions_output=attractions_result.data
    )
    _persist_result(itinerary, "scheduler", {"trip": trip}, scheduler_result.data,
                    scheduler_result.drafts, scheduler_result.issues)
    _progress("scheduler", "done")
    
    # ── Stage 5: Food + Validator (PARALLEL) ────────────────────────
    _progress("food_validator", "started", "Finding restaurants & validating...")
    time.sleep(2)  # Rate limit buffer
    with ThreadPoolExecutor(max_workers=_PARALLEL_WORKERS) as pool:
        food_future = pool.submit(
            _run_agent_safe,
            lambda: food.run(trip=trip, scheduler_output=scheduler_result.data),
            "food",
            {"days": []},
            itinerary, trip
        )
        validator_future = pool.submit(
            _run_agent_safe,
            lambda: validator.run(trip=trip, scheduler_output=scheduler_result.data),
            "validator",
            {"validation": [], "warnings": []},
            itinerary, trip
        )
        food_result = food_future.result()
        validator_result = validator_future.result()
    
    logger.info("Stage 5 complete (Food + Validator ran in parallel)")
    _progress("food_validator", "done")
    
    # ── Stage 6: Budget (sequential — needs scheduler + food) ───────
    _progress("budget", "started", "Calculating costs...")
    time.sleep(1)  # Rate limit buffer
    budget_result = budget.run(trip=trip, scheduler_output=scheduler_result.data, food_output=food_result.data)
    _persist_result(itinerary, "budget", {"trip": trip}, budget_result.data,
                    budget_result.drafts, budget_result.issues)
    _progress("budget", "done")
    
    # ── Travel options ──────────────────────────────────────────────
    _progress("finalizing", "started", "Finalizing your itinerary...")
    travel_data = research.get_travel_options(trip)
    
    # ── Build final response ────────────────────────────────────────
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
    
    # ── Booking deep links ────────────────────────────────────────
    booking_links = generate_booking_links(trip)

    elapsed = time.monotonic() - t_start
    
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
        "booking_links": booking_links,
        "generated_at": datetime.now(timezone.utc).isoformat()
    }
    
    _progress("finalizing", "done", "Your itinerary is ready!")
    logger.info(f"Generation complete for {dest} in {elapsed:.1f}s")
    return response
