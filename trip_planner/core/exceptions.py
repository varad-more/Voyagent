"""
Custom exceptions and exception handler.
"""
import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


class TripPlannerError(Exception):
    """Base exception for Trip Planner."""
    def __init__(self, message: str, code: str = "error"):
        self.message = message
        self.code = code
        super().__init__(message)


class GeminiError(TripPlannerError):
    """Raised when Gemini API fails."""
    def __init__(self, message: str):
        super().__init__(message, "gemini_error")


class ExternalAPIError(TripPlannerError):
    """Raised when an external API call fails."""
    def __init__(self, service: str, message: str):
        self.service = service
        super().__init__(f"{service}: {message}", "external_api_error")


class ValidationError(TripPlannerError):
    """Raised when validation fails."""
    def __init__(self, message: str, field: str = None):
        self.field = field
        super().__init__(message, "validation_error")


def custom_exception_handler(exc, context):
    """Custom DRF exception handler."""
    response = exception_handler(exc, context)
    
    if isinstance(exc, TripPlannerError):
        logger.error(f"Trip Planner Error: {exc.message}")
        return Response(
            {"error": exc.code, "message": exc.message},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if response is None:
        logger.exception(f"Unhandled exception: {exc}")
        return Response(
            {"error": "internal_error", "message": "An unexpected error occurred"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    return response
