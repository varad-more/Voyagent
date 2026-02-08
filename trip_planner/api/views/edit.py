"""
Schedule block editing API view.
"""
import logging
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from trip_planner.services.gemini import gemini_client
from trip_planner.api.serializers import EditBlockRequestSerializer, ScheduleBlockSerializer
from trip_planner.core.utils import best_effort_json

logger = logging.getLogger(__name__)


class EditBlockView(APIView):
    """POST /api/edit/block - Edit schedule block with AI."""
    
    def post(self, request):
        serializer = EditBlockRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"error": "validation_error", "details": serializer.errors},
                          status=status.HTTP_400_BAD_REQUEST)
        
        if not gemini_client.is_available:
            return Response({"error": "AI not available"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        data = serializer.validated_data
        block = data["current_block"]
        
        prompt = f"""
Edit this schedule block based on the instruction.

Block:
- Time: {block.get('start_time')} - {block.get('end_time')}
- Title: {block.get('title')}
- Location: {block.get('location')}
- Description: {block.get('description')}
- Type: {block.get('block_type')}

Destination: {data['destination']}
Instruction: {data['instruction']}

Return updated block as JSON:
{{"start_time": "HH:MM", "end_time": "HH:MM", "title": "", "location": "", "description": "", "block_type": "", "travel_time_mins": 0, "buffer_mins": 0, "micro_activities": []}}
"""
        
        try:
            raw = gemini_client.generate_content(prompt)
            edited = best_effort_json(raw)
            
            block_serializer = ScheduleBlockSerializer(data=edited)
            if not block_serializer.is_valid():
                return Response({"block": block, "warning": "AI response invalid"})
            
            return Response({"block": block_serializer.validated_data, "original": block})
            
        except Exception as e:
            logger.exception(f"Edit failed: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
