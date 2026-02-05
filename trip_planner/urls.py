"""
URL configuration for Trip Planner.
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse


def health_check(request):
    """Health check endpoint."""
    return JsonResponse({"status": "healthy"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health", health_check, name="health"),
    path("api/", include("trip_planner.api.urls")),
]
