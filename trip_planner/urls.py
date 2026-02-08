"""
URL configuration for Trip Planner.
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.shortcuts import render


def health_check(request):
    """Health check endpoint."""
    return JsonResponse({"status": "healthy"})


def home_view(request):
    """Home page with trip planner form."""
    return render(request, "index.html")


urlpatterns = [
    path("", home_view, name="home"),
    path("admin/", admin.site.urls),
    path("health", health_check, name="health"),
    path("api/", include("trip_planner.api.urls")),
]

