"""
SSE (Server-Sent Events) streaming view for real-time itinerary generation progress.
"""
import json
import logging
import queue
import threading

from django.http import StreamingHttpResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from trip_planner.models import Itinerary, ItineraryStatus
from trip_planner.api.serializers import TripRequestSerializer
from trip_planner.services.orchestrator import generate_itinerary
from trip_planner.core.exceptions import GeminiError, GeminiQuotaError

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name="dispatch")
class ItineraryStreamView(View):
    """POST /api/itineraries/stream — generate itinerary with SSE progress updates."""

    http_method_names = ["post"]

    def post(self, request):
        serializer = TripRequestSerializer(data=json.loads(request.body))
        if not serializer.is_valid():
            return StreamingHttpResponse(
                self._sse_error(f"Validation error: {serializer.errors}"),
                content_type="text/event-stream",
                status=400,
            )

        trip_data = self._serialize_trip(serializer.validated_data)

        itinerary = Itinerary.objects.create(
            status=ItineraryStatus.PROCESSING,
            request_json=trip_data,
        )

        # Thread-safe queue for SSE events
        event_queue = queue.Queue()

        def progress_cb(stage: str, status: str, detail: str = ""):
            """Push a progress event onto the queue."""
            event_queue.put({
                "type": "progress",
                "stage": stage,
                "status": status,
                "detail": detail,
            })

        def generate_in_thread():
            """Run the orchestrator in a background thread, pushing events."""
            try:
                result = generate_itinerary(trip_data, itinerary, progress_cb=progress_cb)
                itinerary.mark_completed(result)
                event_queue.put({"type": "result", "data": result})
            except GeminiQuotaError as e:
                logger.error(f"SSE: Gemini Quota Exhausted: {e}")
                itinerary.mark_failed("Quota Exhausted")
                event_queue.put({"type": "error", "message": "AI quota exhausted. Please try again later."})
            except GeminiError as e:
                logger.error(f"SSE: Gemini API error: {e}")
                itinerary.mark_failed(str(e))
                event_queue.put({"type": "error", "message": str(e)})
            except Exception as e:
                logger.exception(f"SSE: Generation failed: {e}")
                itinerary.mark_failed(str(e))
                event_queue.put({"type": "error", "message": str(e)})
            finally:
                event_queue.put(None)  # sentinel — stream is finished

        # Kick off generation in a thread
        thread = threading.Thread(target=generate_in_thread, daemon=True)
        thread.start()

        response = StreamingHttpResponse(
            self._event_stream(event_queue),
            content_type="text/event-stream",
        )
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"  # Disable Nginx buffering
        return response

    # ------------------------------------------------------------------

    @staticmethod
    def _event_stream(event_queue):
        """Generator that yields SSE formatted events from the queue."""
        while True:
            try:
                event = event_queue.get(timeout=120)  # 2-min safety timeout
            except queue.Empty:
                # Send a keep-alive comment to prevent connection drop
                yield ": keepalive\n\n"
                continue

            if event is None:
                # Sentinel — stream is done
                yield "event: done\ndata: {}\n\n"
                return

            event_type = event.get("type", "progress")
            yield f"event: {event_type}\ndata: {json.dumps(event)}\n\n"

    @staticmethod
    def _sse_error(message: str):
        """Yield a single SSE error event."""
        yield f"event: error\ndata: {json.dumps({'type': 'error', 'message': message})}\n\n"
        yield "event: done\ndata: {}\n\n"

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
