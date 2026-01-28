from __future__ import annotations

import datetime as dt

from app.agents.base import AgentResult, BaseAgent
from app.core.gemini import generate_validated
from app.schemas.agents import PlannerOutput
from app.schemas.itinerary import TripRequest


class PlannerAgent(BaseAgent):
    name = "planner"

    async def run(self, *, trip: TripRequest) -> AgentResult:
        if not self.gemini_client:
            days = []
            current = trip.start_date
            while current <= trip.end_date:
                days.append(
                    {
                        "date": current,
                        "theme": "Highlights and local flavor",
                        "must_do": ["Flagship attraction", "Local neighborhood walk"],
                        "optional_stops": ["Cafe break", "Scenic viewpoint"],
                    }
                )
                current += dt.timedelta(days=1)
            output = PlannerOutput(summary=f"Trip plan for {trip.destination}.", days=days)
            return AgentResult(data=output, drafts=[], issues=["gemini_disabled"])

        system = (
            "You are a senior travel planner. Produce a day-by-day skeleton plan with"
            " must-do stops and optional stops. Keep it realistic."
        )
        user = (
            f"Destination: {trip.destination}\n"
            f"Dates: {trip.start_date} to {trip.end_date}\n"
            f"Travelers: {trip.travelers.adults} adults, {trip.travelers.children} children\n"
            f"Interests: {', '.join(trip.activity_preferences.interests)}\n"
            f"Pace: {trip.activity_preferences.pace}\n"
            f"Notes: {trip.notes or 'None'}"
        )
        data, drafts, issues = generate_validated(
            client=self.gemini_client,
            system_prompt=system,
            user_prompt=user,
            model_cls=PlannerOutput,
        )
        return AgentResult(data=data, drafts=drafts, issues=issues)
