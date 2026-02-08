"""
API URL configuration.
"""
from django.urls import path
from .views import (
    ItineraryCreateView, ItineraryGenerateView, ItineraryDetailView, ItineraryICSView,
    ImageAnalysisView, EditBlockView
)

urlpatterns = [
    # Itineraries
    path("itineraries/", ItineraryCreateView.as_view(), name="itinerary-create"),
    path("itineraries/generate", ItineraryGenerateView.as_view(), name="itinerary-generate"),
    path("itineraries/<uuid:itinerary_id>/", ItineraryDetailView.as_view(), name="itinerary-detail"),
    path("itineraries/<uuid:itinerary_id>/ics", ItineraryICSView.as_view(), name="itinerary-ics"),
    
    # Analysis
    path("analysis/image", ImageAnalysisView.as_view(), name="analysis-image"),
    
    # Edit
    path("edit/block", EditBlockView.as_view(), name="edit-block"),
]
