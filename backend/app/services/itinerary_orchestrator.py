from __future__ import annotations

import datetime as dt
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.attractions import AttractionsAgent
from app.agents.budget import BudgetAgent
from app.agents.food import FoodAgent
from app.agents.planner import PlannerAgent
from app.agents.research import ResearchAgent
from app.agents.scheduler import SchedulerAgent
from app.agents.validator import ValidatorAgent
from app.agents.weather import WeatherAgent
from app.core.config import get_settings
from app.core.gemini import GeminiClient
from app.models.trace import AgentTrace
from app.schemas.agents import OrchestratorOutput
from app.schemas.itinerary import DayPlan, ItineraryResponse, TravelOption, TripRequest


logger = structlog.get_logger(__name__)


def _build_packing_list(weather_payload: dict[str, Any], trip: TripRequest) -> list[str]:
    packing = {"Comfortable walking shoes", "Reusable water bottle", "Portable phone charger"}
    for day in weather_payload.get("daily", []):
        high = day.get("high_c", 20)
        low = day.get("low_c", 10)
        if high >= 28:
            packing.update({"Lightweight breathable outfits", "Sunhat", "Sunscreen"})
        if low <= 8:
            packing.update({"Warm jacket", "Thermal layers", "Beanie"})
        if day.get("precipitation_chance", 0) >= 0.4:
            packing.update({"Packable rain jacket", "Umbrella"})
    if trip.activity_preferences.pace == "fast":
        packing.add("Compression socks for long walking days")
    if trip.activity_preferences.accessibility_needs:
        packing.add("Mobility aids and comfort items")
    return sorted(packing)


async def _store_trace(
    *,
    session: AsyncSession,
    itinerary_id: int,
    agent_name: str,
    step_name: str,
    input_json: dict | None,
    output_json: dict | None,
    issues: str | None,
) -> None:
    session.add(
        AgentTrace(
            itinerary_id=itinerary_id,
            agent_name=agent_name,
            step_name=step_name,
            input_json=input_json,
            output_json=output_json,
            issues=issues,
        )
    )


async def _persist_agent_result(
    *,
    session: AsyncSession,
    itinerary_id: int,
    agent_name: str,
    input_payload: dict[str, Any],
    output_payload: dict[str, Any],
    drafts: list[str],
    issues: list[str],
) -> None:
    for idx, draft in enumerate(drafts):
        await _store_trace(
            session=session,
            itinerary_id=itinerary_id,
            agent_name=agent_name,
            step_name=f"draft_{idx + 1}",
            input_json=input_payload,
            output_json={"draft": draft},
            issues=None,
        )
    await _store_trace(
        session=session,
        itinerary_id=itinerary_id,
        agent_name=agent_name,
        step_name="final",
        input_json=input_payload,
        output_json=output_payload,
        issues="; ".join(issues) if issues else None,
    )


async def generate_itinerary(
    *,
    trip: TripRequest,
    itinerary_id: int,
    session: AsyncSession,
) -> ItineraryResponse:
    settings = get_settings()
    gemini_client = None
    if settings.gemini_api_key:
        try:
            gemini_client = GeminiClient()
        except RuntimeError as exc:
            logger.warning("gemini_unavailable", error=str(exc))

    planner_agent = PlannerAgent(gemini_client)
    research_agent = ResearchAgent(gemini_client)
    weather_agent = WeatherAgent(gemini_client)
    attractions_agent = AttractionsAgent(gemini_client)
    scheduler_agent = SchedulerAgent(gemini_client)
    food_agent = FoodAgent(gemini_client)
    budget_agent = BudgetAgent(gemini_client)
    validator_agent = ValidatorAgent()

    research_context = ""
    if gemini_client:
        research_context = await research_agent.conduct_research(trip, session)
        await _store_trace(
            session=session,
            itinerary_id=itinerary_id,
            agent_name="research_agent",
            step_name="final",
            input_json={"trip": trip.model_dump(mode="json")},
            output_json={"research_context": research_context},
            issues=None,
        )

    planner_result = await planner_agent.run(trip=trip, research_context=research_context)
    await _persist_agent_result(
        session=session,
        itinerary_id=itinerary_id,
        agent_name=planner_agent.name,
        input_payload={"trip": trip.model_dump(mode="json")},
        output_payload=planner_result.data.model_dump(mode="json"),
        drafts=planner_result.drafts,
        issues=planner_result.issues,
    )

    weather_result = await weather_agent.run(trip=trip, session=session)
    await _persist_agent_result(
        session=session,
        itinerary_id=itinerary_id,
        agent_name=weather_agent.name,
        input_payload={"trip": trip.model_dump(mode="json")},
        output_payload=weather_result.data.model_dump(mode="json"),
        drafts=weather_result.drafts,
        issues=weather_result.issues,
    )

    attractions_result = await attractions_agent.run(trip=trip, session=session)
    await _persist_agent_result(
        session=session,
        itinerary_id=itinerary_id,
        agent_name=attractions_agent.name,
        input_payload={"trip": trip.model_dump(mode="json")},
        output_payload=attractions_result.data.model_dump(mode="json"),
        drafts=attractions_result.drafts,
        issues=attractions_result.issues,
    )

    scheduler_result = await scheduler_agent.run(
        trip=trip,
        planner=planner_result.data,
        weather_summary=weather_result.data.weather.overview,
    )
    await _persist_agent_result(
        session=session,
        itinerary_id=itinerary_id,
        agent_name=scheduler_agent.name,
        input_payload={
            "trip": trip.model_dump(mode="json"),
            "planner": planner_result.data.model_dump(mode="json"),
            "weather": weather_result.data.model_dump(mode="json"),
        },
        output_payload=scheduler_result.data.model_dump(mode="json"),
        drafts=scheduler_result.drafts,
        issues=scheduler_result.issues,
    )

    food_result = await food_agent.run(trip=trip, scheduler_output=scheduler_result.data)
    await _persist_agent_result(
        session=session,
        itinerary_id=itinerary_id,
        agent_name=food_agent.name,
        input_payload={
            "trip": trip.model_dump(mode="json"),
            "schedule": scheduler_result.data.model_dump(mode="json"),
        },
        output_payload=food_result.data.model_dump(mode="json"),
        drafts=food_result.drafts,
        issues=food_result.issues,
    )

    budget_result = await budget_agent.run(
        trip=trip,
        scheduler_output=scheduler_result.data,
        food_output=food_result.data,
    )
    await _persist_agent_result(
        session=session,
        itinerary_id=itinerary_id,
        agent_name=budget_agent.name,
        input_payload={
            "trip": trip.model_dump(mode="json"),
            "schedule": scheduler_result.data.model_dump(mode="json"),
            "meals": food_result.data.model_dump(mode="json"),
        },
        output_payload=budget_result.data.model_dump(mode="json"),
        drafts=budget_result.drafts,
        issues=budget_result.issues,
    )

    validator_result = await validator_agent.run(trip=trip, scheduler_output=scheduler_result.data)
    await _persist_agent_result(
        session=session,
        itinerary_id=itinerary_id,
        agent_name=validator_agent.name,
        input_payload={"trip": trip.model_dump(mode="json"), "schedule": scheduler_result.data.model_dump(mode="json")},
        output_payload=validator_result.data.model_dump(mode="json"),
        drafts=validator_result.drafts,
        issues=validator_result.issues,
    )

    days: list[DayPlan] = []
    meals_by_date = {day.date: day.meals for day in food_result.data.days}
    for day in scheduler_result.data.days:
        days.append(
            DayPlan(
                date=day.date,
                title=f"{trip.destination} day plan",
                weather_summary=day.weather_summary,
                contingencies=weather_result.data.adjustments,
                schedule=day.schedule,
                meals=meals_by_date.get(day.date, []),
                notes=day.notes,
            )
        )

    packing_list = _build_packing_list(weather_result.data.weather.model_dump(), trip)

    # Generate travel options (cars, hotels, flights) AND transport analysis
    travel_data = await research_agent.get_travel_options(trip, session)
    
    # Extract lists from the dictionary response
    booking_options_raw = travel_data.get("booking_options", [])
    transport_analysis_raw = travel_data.get("transport_analysis")

    travel_options = [
        TravelOption(
            type=opt.get("type", "hotel"),
            name=opt.get("name", "Unknown"),
            provider=opt.get("provider", "Unknown"),
            price_estimate=opt.get("price_estimate", "N/A"),
            details=opt.get("details", ""),
            booking_url=opt.get("booking_url"),
            rating=opt.get("rating"),
            features=opt.get("features", []),
        )
        for opt in booking_options_raw
    ]

    orchestrator_output = OrchestratorOutput(
        summary=planner_result.data.summary,
        days=days,
        weather=weather_result.data.weather,
        attractions=attractions_result.data.attractions,
        packing_list=packing_list,
        budget=budget_result.data.budget,
        validation=validator_result.data.validation,
        warnings=validator_result.data.warnings,
    )

    response = ItineraryResponse(
        itinerary_id=itinerary_id,
        summary=orchestrator_output.summary,
        days=orchestrator_output.days,
        weather=orchestrator_output.weather,
        attractions=orchestrator_output.attractions,
        packing_list=orchestrator_output.packing_list,
        budget=orchestrator_output.budget,
        validation=orchestrator_output.validation,
        warnings=orchestrator_output.warnings,
        travel_options=travel_options,
        transport_analysis=transport_analysis_raw,
        generated_at=dt.datetime.now(dt.timezone.utc),
    )
    return response
