"""
API Serializers for request/response handling.
"""
from rest_framework import serializers
from datetime import date, time
from trip_planner.models import Itinerary


# === Request Serializers ===

class TravelersSerializer(serializers.Serializer):
    adults = serializers.IntegerField(min_value=1)
    children = serializers.IntegerField(min_value=0, default=0)


class FoodPreferencesSerializer(serializers.Serializer):
    cuisines = serializers.ListField(child=serializers.CharField(), default=list)
    dietary_restrictions = serializers.ListField(child=serializers.CharField(), default=list)
    avoid_ingredients = serializers.ListField(child=serializers.CharField(), default=list)


class ActivityPreferencesSerializer(serializers.Serializer):
    interests = serializers.ListField(child=serializers.CharField(), default=list)
    pace = serializers.ChoiceField(choices=["slow", "moderate", "fast"], default="moderate")
    accessibility_needs = serializers.ListField(child=serializers.CharField(), default=list)


class LodgingPreferencesSerializer(serializers.Serializer):
    lodging_type = serializers.ChoiceField(
        choices=["hotel", "hostel", "apartment", "boutique", "any"], default="any")
    max_distance_km_from_center = serializers.FloatField(min_value=0, default=5.0)


class BudgetPreferencesSerializer(serializers.Serializer):
    currency = serializers.CharField(min_length=3, max_length=3, default="USD")
    total_budget = serializers.FloatField(min_value=0)
    comfort_level = serializers.ChoiceField(choices=["budget", "midrange", "luxury"], default="midrange")


class TripRequestSerializer(serializers.Serializer):
    destination = serializers.CharField(max_length=500)
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    travelers = TravelersSerializer()
    origin_location = serializers.CharField(max_length=500, required=False, allow_null=True)
    food_preferences = FoodPreferencesSerializer(required=False, default=dict)
    activity_preferences = ActivityPreferencesSerializer(required=False, default=dict)
    lodging_preferences = LodgingPreferencesSerializer(required=False, default=dict)
    budget = BudgetPreferencesSerializer()
    daily_start_time = serializers.TimeField(default=time(9, 0))
    daily_end_time = serializers.TimeField(default=time(20, 0))
    notes = serializers.CharField(max_length=2000, required=False, allow_null=True, allow_blank=True)
    
    def validate(self, data):
        if data["start_date"] > data["end_date"]:
            raise serializers.ValidationError({"end_date": "Must be after start date"})
        if data["start_date"] < date.today():
            raise serializers.ValidationError({"start_date": "Cannot be in the past"})
        return data


# === Model Serializers ===

class ItinerarySerializer(serializers.ModelSerializer):
    request = serializers.JSONField(source="request_json")
    result = serializers.JSONField(source="result_json", required=False, allow_null=True)
    
    class Meta:
        model = Itinerary
        fields = ["id", "status", "request", "result", "error_message", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


# === Other Serializers ===

class ScheduleBlockSerializer(serializers.Serializer):
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    title = serializers.CharField()
    location = serializers.CharField()
    description = serializers.CharField()
    block_type = serializers.ChoiceField(choices=["activity", "meal", "travel", "rest", "buffer"])
    travel_time_mins = serializers.IntegerField(min_value=0, default=0)
    buffer_mins = serializers.IntegerField(min_value=0, default=0)
    micro_activities = serializers.ListField(default=list)


class EditBlockRequestSerializer(serializers.Serializer):
    day_index = serializers.IntegerField(min_value=0)
    block_index = serializers.IntegerField(min_value=0)
    instruction = serializers.CharField(max_length=1000)
    current_block = ScheduleBlockSerializer()
    destination = serializers.CharField(max_length=500)


class ImageAnalysisResponseSerializer(serializers.Serializer):
    destination = serializers.CharField(required=False, allow_null=True)
    interests = serializers.ListField(child=serializers.CharField(), default=list)
    vibe = serializers.CharField(required=False, allow_null=True)
    season = serializers.CharField(required=False, allow_null=True)
    activities = serializers.ListField(child=serializers.CharField(), default=list)
