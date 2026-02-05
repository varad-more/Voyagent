"""
Image analysis API view.
"""
import logging
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser

from trip_planner.services.gemini import gemini_client
from trip_planner.api.serializers import ImageAnalysisResponseSerializer
from trip_planner.core.utils import best_effort_json

logger = logging.getLogger(__name__)


class ImageAnalysisView(APIView):
    """POST /api/analysis/image - Analyze travel image."""
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request):
        if "image" not in request.FILES:
            return Response({"error": "No image provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        image_file = request.FILES["image"]
        
        # Validate
        allowed = ["image/jpeg", "image/png", "image/webp", "image/gif"]
        if image_file.content_type not in allowed:
            return Response({"error": f"Invalid type: {image_file.content_type}"},
                          status=status.HTTP_400_BAD_REQUEST)
        
        if image_file.size > 10 * 1024 * 1024:  # 10MB
            return Response({"error": "Image too large (max 10MB)"},
                          status=status.HTTP_400_BAD_REQUEST)
        
        if not gemini_client.is_available:
            return Response({"error": "AI not available"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        prompt = """
Analyze this travel image and extract:
- destination: place shown or suggested
- interests: activities/interests suggested
- vibe: atmosphere (romantic, adventurous, relaxing, etc.)
- season: ideal season
- activities: specific activities visible

Return JSON: {"destination": str|null, "interests": [], "vibe": str|null, "season": str|null, "activities": []}
"""
        
        try:
            raw = gemini_client.generate_from_image(image_file.read(), prompt)
            data = best_effort_json(raw)
            
            result = {
                "destination": data.get("destination"),
                "interests": data.get("interests", []),
                "vibe": data.get("vibe"),
                "season": data.get("season"),
                "activities": data.get("activities", [])
            }
            
            return Response(result)
            
        except Exception as e:
            logger.exception(f"Image analysis failed: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
