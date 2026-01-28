from __future__ import annotations

from app.agents.base import AgentResult, BaseAgent
from app.core.gemini import generate_validated
from app.schemas.agents import AttractionsAgentOutput
from app.schemas.itinerary import Attraction, TripRequest
from app.services.places import get_attractions


class AttractionsAgent(BaseAgent):
    name = "attractions"

    async def run(self, *, trip: TripRequest, session) -> AgentResult:
        places_payload = await get_attractions(
            destination=trip.destination,
            interests=trip.activity_preferences.interests,
            session=session,
        )

        if not self.gemini_client:
            attractions = [Attraction.model_validate(item) for item in places_payload["attractions"]]
            output = AttractionsAgentOutput(attractions=attractions)
            return AgentResult(data=output, drafts=[], issues=["gemini_disabled"])

        system = (
            "You are a travel curator. Rank nearby attractions by fit and distance."
            " Provide a reason and a normalized score."
        )
        user = (
            f"Destination: {trip.destination}\n"
            f"Traveler interests: {trip.activity_preferences.interests}\n"
            f"Places data: {places_payload}"
        )
        data, drafts, issues = generate_validated(
            client=self.gemini_client,
            system_prompt=system,
            user_prompt=user,
            model_cls=AttractionsAgentOutput,
        )
        return AgentResult(data=data, drafts=drafts, issues=issues)
