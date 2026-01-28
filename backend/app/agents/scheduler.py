from __future__ import annotations

import datetime as dt

from app.agents.base import AgentResult, BaseAgent
from app.core.config import get_settings
from app.core.gemini import generate_validated
from app.schemas.agents import PlannerOutput, SchedulerOutput
from app.schemas.itinerary import ScheduleBlock, TripRequest


class SchedulerAgent(BaseAgent):
    name = "scheduler"

    async def run(
        self,
        *,
        trip: TripRequest,
        planner: PlannerOutput,
        weather_summary: str,
    ) -> AgentResult:
        if not self.gemini_client:
            days = []
            for day in planner.days:
                blocks = [
                    ScheduleBlock(
                        start_time=dt.time(9, 0),
                        end_time=dt.time(11, 30),
                        title=day.must_do[0] if day.must_do else "City highlights",
                        location=trip.destination,
                        description="Primary activity block.",
                        block_type="activity",
                        travel_time_mins=20,
                        buffer_mins=15,
                        micro_activities=[],
                    ),
                    ScheduleBlock(
                        start_time=dt.time(12, 0),
                        end_time=dt.time(13, 30),
                        title="Lunch break",
                        location=trip.destination,
                        description="Local dining aligned with dietary needs.",
                        block_type="meal",
                        travel_time_mins=10,
                        buffer_mins=10,
                        micro_activities=[],
                    ),
                    ScheduleBlock(
                        start_time=dt.time(14, 0),
                        end_time=dt.time(17, 30),
                        title=day.optional_stops[0] if day.optional_stops else "Neighborhood stroll",
                        location=trip.destination,
                        description="Flexible afternoon exploration.",
                        block_type="activity",
                        travel_time_mins=20,
                        buffer_mins=20,
                        micro_activities=[],
                    ),
                ]
                days.append(
                    {
                        "date": day.date,
                        "weather_summary": weather_summary,
                        "schedule": blocks,
                        "notes": [f"Theme: {day.theme}"],
                    }
                )
            output = SchedulerOutput.model_validate({"days": days})
            return AgentResult(data=output, drafts=[], issues=["gemini_disabled"])

        settings = get_settings()
        system = (
            "You are an expert trip scheduler. Convert the skeleton plan into a timed"
            " schedule with travel time and buffers. Respect daily time windows and"
            " avoid impossible overlaps."
        )
        user = (
            f"Destination: {trip.destination}\n"
            f"Daily window: {trip.daily_start_time} - {trip.daily_end_time}\n"
            f"Buffer minutes default: {settings.planner_buffer_minutes}\n"
            f"Weather summary: {weather_summary}\n"
            f"Planner output: {planner.model_dump()}"
        )
        data, drafts, issues = generate_validated(
            client=self.gemini_client,
            system_prompt=system,
            user_prompt=user,
            model_cls=SchedulerOutput,
        )
        return AgentResult(data=data, drafts=drafts, issues=issues)
