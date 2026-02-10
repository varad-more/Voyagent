"""
API URL configuration.
"""
from django.urls import path
from .views import (
    ItineraryCreateView, ItineraryGenerateView, ItineraryDetailView, ItineraryICSView,
    ImageAnalysisView, EditBlockView,
    SwapBlockView, RegenerateDayView,
    ItineraryStreamView,
)
from .views.places import PlacesAutocompleteView

urlpatterns = [
    # Itineraries
    path("itineraries/", ItineraryCreateView.as_view(), name="itinerary-create"),
    path("itineraries/generate", ItineraryGenerateView.as_view(), name="itinerary-generate"),
    path("itineraries/stream", ItineraryStreamView.as_view(), name="itinerary-stream"),
    path("itineraries/<uuid:itinerary_id>/", ItineraryDetailView.as_view(), name="itinerary-detail"),
    path("itineraries/<uuid:itinerary_id>/ics", ItineraryICSView.as_view(), name="itinerary-ics"),
    
    # Analysis
    path("analysis/image", ImageAnalysisView.as_view(), name="analysis-image"),
    
    # Edit
    path("edit/block", EditBlockView.as_view(), name="edit-block"),
    
    # Swap / Regenerate
    path("edit/swap", SwapBlockView.as_view(), name="swap-block"),
    path("edit/regenerate-day", RegenerateDayView.as_view(), name="regenerate-day"),
    
    # Places
    path("places/autocomplete", PlacesAutocompleteView.as_view(), name="places-autocomplete"),
]
