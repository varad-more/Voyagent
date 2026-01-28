from __future__ import annotations

import datetime as dt

from app.agents.base import AgentResult, BaseAgent
from app.core.gemini import generate_validated
from app.schemas.agents import FoodOutput
from app.schemas.itinerary import MealPlan, TripRequest


class FoodAgent(BaseAgent):
    name = "food"

    async def run(self, *, trip: TripRequest, scheduler_output) -> AgentResult:
        if not self.gemini_client:
            days = []
            for day in scheduler_output.days:
                meals = [
                    MealPlan(
                        time=dt.time(8, 30),
                        name="Local breakfast cafe",
                        cuisine="Local",
                        dietary_fit=trip.food_preferences.dietary_restrictions,
                        location=trip.destination,
                        reservation_needed=False,
                        estimated_cost=12,
                    ),
                    MealPlan(
                        time=dt.time(12, 30),
                        name="Neighborhood bistro",
                        cuisine="Regional",
                        dietary_fit=trip.food_preferences.dietary_restrictions,
                        location=trip.destination,
                        reservation_needed=False,
                        estimated_cost=20,
                    ),
                    MealPlan(
                        time=dt.time(19, 0),
                        name="Signature dinner spot",
                        cuisine="Contemporary",
                        dietary_fit=trip.food_preferences.dietary_restrictions,
                        location=trip.destination,
                        reservation_needed=True,
                        estimated_cost=35,
                    ),
                ]
                days.append({"date": day.date, "meals": meals})
            output = FoodOutput.model_validate({"days": days})
            return AgentResult(data=output, drafts=[], issues=["gemini_disabled"])

        system = (
            "You are a food planner. Add meals aligned to the schedule and dietary"
            " constraints. Provide realistic meal times."
        )
        user = (
            f"Destination: {trip.destination}\n"
            f"Dietary restrictions: {trip.food_preferences.dietary_restrictions}\n"
            f"Cuisines: {trip.food_preferences.cuisines}\n"
            f"Schedule: {scheduler_output.model_dump()}"
        )
        data, drafts, issues = generate_validated(
            client=self.gemini_client,
            system_prompt=system,
            user_prompt=user,
            model_cls=FoodOutput,
        )
        return AgentResult(data=data, drafts=drafts, issues=issues)
