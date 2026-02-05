"""
Django Admin configuration.
"""
from django.contrib import admin
from .models import Itinerary, AgentTrace, ExternalCache


@admin.register(Itinerary)
class ItineraryAdmin(admin.ModelAdmin):
    list_display = ["id", "destination", "status", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["id"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(AgentTrace)
class AgentTraceAdmin(admin.ModelAdmin):
    list_display = ["id", "itinerary", "agent_name", "step_name", "created_at"]
    list_filter = ["agent_name", "created_at"]
    readonly_fields = ["id", "created_at"]


@admin.register(ExternalCache)
class ExternalCacheAdmin(admin.ModelAdmin):
    list_display = ["cache_key", "source", "expires_at", "is_expired"]
    list_filter = ["source"]
    search_fields = ["cache_key"]
    
    def is_expired(self, obj):
        return obj.is_expired
    is_expired.boolean = True
