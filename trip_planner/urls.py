"""
URL configuration for Trip Planner.
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404

from trip_planner.models import Itinerary


def health_check(request):
    """Health check endpoint."""
    return JsonResponse({"status": "healthy"})


def home_view(request):
    """Home page with trip planner form."""
    return render(request, "index.html")


def share_view(request, itinerary_id):
    """Public read-only share page for an itinerary."""
    itinerary = get_object_or_404(Itinerary, id=itinerary_id)
    return render(request, "share.html", {
        "itinerary": itinerary,
        "result_json": itinerary.result_json or {},
        "request_json": itinerary.request_json or {},
    })


urlpatterns = [
    path("", home_view, name="home"),
    path("admin/", admin.site.urls),
    path("health", health_check, name="health"),
    path("api/", include("trip_planner.api.urls")),
    path("share/<uuid:itinerary_id>/", share_view, name="share-itinerary"),
]

