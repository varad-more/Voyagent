from __future__ import annotations

from app.agents.base import AgentResult, BaseAgent
from app.core.gemini import generate_validated
from app.schemas.agents import WeatherAgentOutput
from app.schemas.itinerary import TripRequest, WeatherSummary
from app.services.weather import get_weather


class WeatherAgent(BaseAgent):
    name = "weather"

    async def run(self, *, trip: TripRequest, session) -> AgentResult:
        weather_payload = await get_weather(
            destination=trip.destination,
            start_date=trip.start_date,
            end_date=trip.end_date,
            session=session,
        )

        if not self.gemini_client:
            risks = [
                "Pack a light rain jacket in case of showers.",
            ]
            weather = WeatherSummary.model_validate(weather_payload)
            output = WeatherAgentOutput(weather=weather, adjustments=risks)
            return AgentResult(data=output, drafts=[], issues=["gemini_disabled"])

        system = (
            "You are a travel weather analyst. Summarize risks and propose schedule"
            " adjustments based on the forecast."
        )
        user = (
            f"Destination: {trip.destination}\n"
            f"Forecast JSON: {weather_payload}"
        )
        data, drafts, issues = generate_validated(
            client=self.gemini_client,
            system_prompt=system,
            user_prompt=user,
            model_cls=WeatherAgentOutput,
        )
        return AgentResult(data=data, drafts=drafts, issues=issues)
