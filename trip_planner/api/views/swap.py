"""
Swap / Regenerate schedule block API view.
Generates alternative suggestions for a given schedule block.
"""
import logging
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from trip_planner.services.gemini import gemini_client
from trip_planner.core.utils import best_effort_json

logger = logging.getLogger(__name__)


class SwapBlockView(APIView):
    """POST /api/edit/swap - Generate alternative blocks for a schedule item."""

    def post(self, request):
        data = request.data
        block = data.get("current_block")
        destination = data.get("destination", "Unknown")
        block_type = data.get("block_type", "activity")
        day_date = data.get("day_date", "")
        preferences = data.get("preferences", "")

        if not block:
            return Response(
                {"error": "current_block is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not gemini_client.is_available:
            return Response(
                {"error": "AI not available"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        prompt = f"""
You are a travel planning assistant. The user wants ALTERNATIVE suggestions to replace
a schedule block in their itinerary. Generate exactly 3 different alternatives.

Current block they want to replace:
- Time: {block.get('start_time', '10:00')} - {block.get('end_time', '12:00')}
- Title: {block.get('title', 'Activity')}
- Location: {block.get('location', '')}
- Description: {block.get('description', '')}
- Type: {block_type}

Context:
- Destination: {destination}
- Date: {day_date}
- User preferences: {preferences}

Requirements:
- Keep the SAME time slot ({block.get('start_time', '10:00')} - {block.get('end_time', '12:00')})
- Each alternative should be meaningfully DIFFERENT from the current and from each other
- Include a mix: one popular option, one hidden-gem, one unique/creative option
- Match the block_type ({block_type}) unless it's a meal — then suggest different restaurants/cuisines

Return JSON:
{{
  "alternatives": [
    {{
      "start_time": "HH:MM",
      "end_time": "HH:MM",
      "title": "string",
      "location": "string",
      "description": "string",
      "block_type": "{block_type}",
      "micro_activities": [],
      "why": "Brief reason why this is a good alternative"
    }}
  ]
}}
"""

        try:
            raw = gemini_client.generate_content(prompt)
            parsed = best_effort_json(raw)
            alternatives = parsed.get("alternatives", [])

            # Ensure we have at most 3 alternatives with required fields
            cleaned = []
            for alt in alternatives[:3]:
                cleaned.append({
                    "start_time": alt.get("start_time", block.get("start_time", "10:00")),
                    "end_time": alt.get("end_time", block.get("end_time", "12:00")),
                    "title": alt.get("title", "Alternative activity"),
                    "location": alt.get("location", destination),
                    "description": alt.get("description", ""),
                    "block_type": alt.get("block_type", block_type),
                    "micro_activities": alt.get("micro_activities", []),
                    "why": alt.get("why", ""),
                })

            return Response({"alternatives": cleaned, "original": block})

        except Exception as e:
            logger.exception(f"Swap failed: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class RegenerateDayView(APIView):
    """POST /api/edit/regenerate-day - Regenerate the schedule for a single day."""

    def post(self, request):
        data = request.data
        day = data.get("day")
        destination = data.get("destination", "Unknown")
        preferences = data.get("preferences", {})
        weather_summary = data.get("weather_summary", "")

        if not day:
            return Response(
                {"error": "day data is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not gemini_client.is_available:
            return Response(
                {"error": "AI not available"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        prompt = f"""
You are a travel planning assistant. Regenerate a completely new schedule for this
day of the trip, keeping the same date but creating fresh activities.

Current day:
- Date: {day.get('date', '')}
- Theme: {day.get('theme', '')}
- Weather: {weather_summary}
- Current blocks: {day.get('blocks', [])}

Context:
- Destination: {destination}
- User preferences: {preferences}

Requirements:
- Same date, same general time window
- Create a DIFFERENT and fresh schedule — don't repeat the same activities
- Include a mix of activities, meals, and rest
- Each block needs: start_time, end_time, title, location, description, block_type, micro_activities

Return JSON:
{{
  "date": "{day.get('date', '')}",
  "day_number": {day.get('day_number', 1)},
  "theme": "A new theme for this day",
  "weather_summary": "{weather_summary}",
  "blocks": [
    {{
      "start_time": "HH:MM",
      "end_time": "HH:MM",
      "title": "string",
      "location": "string",
      "description": "string",
      "block_type": "activity|meal|travel|rest",
      "micro_activities": []
    }}
  ]
}}
"""

        try:
            raw = gemini_client.generate_content(prompt)
            parsed = best_effort_json(raw)

            # Ensure the response has the expected shape
            result = {
                "date": parsed.get("date", day.get("date", "")),
                "day_number": parsed.get("day_number", day.get("day_number", 1)),
                "theme": parsed.get("theme", "Refreshed itinerary"),
                "weather_summary": parsed.get("weather_summary", weather_summary),
                "blocks": parsed.get("blocks", []),
            }

            return Response({"day": result})

        except Exception as e:
            logger.exception(f"Regenerate day failed: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
