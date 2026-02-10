"""
API Views.
"""
from .itineraries import ItineraryCreateView, ItineraryGenerateView, ItineraryDetailView, ItineraryICSView
from .analysis import ImageAnalysisView
from .edit import EditBlockView
from .swap import SwapBlockView, RegenerateDayView
from .stream import ItineraryStreamView

__all__ = [
    "ItineraryCreateView", "ItineraryGenerateView", "ItineraryDetailView", "ItineraryICSView",
    "ImageAnalysisView", "EditBlockView",
    "SwapBlockView", "RegenerateDayView",
    "ItineraryStreamView",
]
