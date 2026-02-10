"""
Itinerary API views.
"""
import logging
from django.http import HttpResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from trip_planner.models import Itinerary, ItineraryStatus
from trip_planner.api.serializers import TripRequestSerializer, ItinerarySerializer
from trip_planner.services.orchestrator import generate_itinerary
from trip_planner.core.utils import build_ics
from trip_planner.core.exceptions import GeminiError, GeminiQuotaError

logger = logging.getLogger(__name__)


class ItineraryCreateView(APIView):
    """POST /api/itineraries/ - Queue async generation."""
    
    def post(self, request):
        serializer = TripRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"error": "validation_error", "details": serializer.errors},
                          status=status.HTTP_400_BAD_REQUEST)
        
        trip_data = self._serialize_trip(serializer.validated_data)
        itinerary = Itinerary.objects.create(
            status=ItineraryStatus.QUEUED,
            request_json=trip_data
        )
        
        return Response(ItinerarySerializer(itinerary).data, status=status.HTTP_201_CREATED)
    
    @staticmethod
    def _serialize_trip(data: dict) -> dict:
        """Convert date/time objects to ISO strings for JSON storage."""
        result = dict(data)
        for key in ["start_date", "end_date"]:
            if key in result and hasattr(result[key], "isoformat"):
                result[key] = result[key].isoformat()
        for key in ["daily_start_time", "daily_end_time"]:
            if key in result and hasattr(result[key], "isoformat"):
                result[key] = result[key].isoformat()
        return result


class ItineraryGenerateView(APIView):
    """POST /api/itineraries/generate - Synchronous generation."""
    
    def post(self, request):
        serializer = TripRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"error": "validation_error", "details": serializer.errors},
                          status=status.HTTP_400_BAD_REQUEST)
        
        trip_data = self._serialize_trip(serializer.validated_data)
        
        itinerary = Itinerary.objects.create(
            status=ItineraryStatus.PROCESSING,
            request_json=trip_data
        )
        
        try:
            result = generate_itinerary(trip_data, itinerary)
            itinerary.mark_completed(result)
            return Response(result)
        except GeminiQuotaError as e:
            logger.error(f"Gemini Quota Exhausted: {e}")
            itinerary.mark_failed("Quota Exhausted")
            return Response(
                {"error": "quota_exhausted", "message": "The AI is currently overloaded (Quota Exhausted). Please try again in a few moments.", "code": "gemini_quota_exhausted"},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        except GeminiError as e:
            logger.error(f"Gemini API error: {e}")
            itinerary.mark_failed(str(e))
            return Response(
                {"error": "gemini_error", "message": str(e), "code": "gemini_not_configured"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            logger.exception(f"Generation failed: {e}")
            itinerary.mark_failed(str(e))
            return Response({"error": "generation_failed", "message": str(e)},
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _serialize_trip(self, data: dict) -> dict:
        """Convert to JSON-serializable format."""
        result = dict(data)
        for key in ["start_date", "end_date"]:
            if key in result and hasattr(result[key], "isoformat"):
                result[key] = result[key].isoformat()
        for key in ["daily_start_time", "daily_end_time"]:
            if key in result and hasattr(result[key], "isoformat"):
                result[key] = result[key].isoformat()
        return result


class ItineraryDetailView(APIView):
    """GET/PATCH /api/itineraries/<id>/"""
    
    def get(self, request, itinerary_id):
        try:
            itinerary = Itinerary.objects.get(id=itinerary_id)
        except Itinerary.DoesNotExist:
            return Response({"error": "not_found"}, status=status.HTTP_404_NOT_FOUND)
        
        return Response(ItinerarySerializer(itinerary).data)
    
    def patch(self, request, itinerary_id):
        try:
            itinerary = Itinerary.objects.get(id=itinerary_id)
        except Itinerary.DoesNotExist:
            return Response({"error": "not_found"}, status=status.HTTP_404_NOT_FOUND)
        
        if "result" in request.data:
            itinerary.result_json = request.data["result"]
            itinerary.save(update_fields=["result_json", "updated_at"])
        
        return Response(ItinerarySerializer(itinerary).data)


class ItineraryICSView(APIView):
    """GET /api/itineraries/<id>/ics - Download ICS calendar."""
    
    def get(self, request, itinerary_id):
        try:
            itinerary = Itinerary.objects.get(id=itinerary_id)
        except Itinerary.DoesNotExist:
            return Response({"error": "not_found"}, status=status.HTTP_404_NOT_FOUND)
        
        if not itinerary.result_json:
            return Response({"error": "no_result"}, status=status.HTTP_400_BAD_REQUEST)
        
        ics_content = build_ics(itinerary.result_json)
        dest = itinerary.request_json.get("destination", "trip").replace(" ", "_")
        
        response = HttpResponse(ics_content, content_type="text/calendar")
        response["Content-Disposition"] = f'attachment; filename="{dest}_itinerary.ics"'
        return response
