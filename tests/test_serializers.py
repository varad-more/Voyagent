"""
Tests for API serializers and request validation.
"""
import pytest
from datetime import date, time, timedelta

from trip_planner.api.serializers import (
    TripRequestSerializer,
    TravelersSerializer,
    BudgetPreferencesSerializer,
    ActivityPreferencesSerializer,
)


def _future(days=30):
    return (date.today() + timedelta(days=days)).isoformat()


class TestTripRequestSerializer:
    def test_valid_request(self, sample_trip):
        s = TripRequestSerializer(data=sample_trip)
        assert s.is_valid(), s.errors

    def test_missing_destination(self, sample_trip):
        del sample_trip["destination"]
        s = TripRequestSerializer(data=sample_trip)
        assert not s.is_valid()
        assert "destination" in s.errors

    def test_missing_start_date(self, sample_trip):
        del sample_trip["start_date"]
        s = TripRequestSerializer(data=sample_trip)
        assert not s.is_valid()
        assert "start_date" in s.errors

    def test_end_before_start(self, sample_trip):
        sample_trip["start_date"] = _future(35)
        sample_trip["end_date"] = _future(30)
        s = TripRequestSerializer(data=sample_trip)
        assert not s.is_valid()

    def test_start_date_in_past(self, sample_trip):
        sample_trip["start_date"] = (date.today() - timedelta(days=1)).isoformat()
        sample_trip["end_date"] = date.today().isoformat()
        s = TripRequestSerializer(data=sample_trip)
        assert not s.is_valid()

    def test_missing_budget(self, sample_trip):
        del sample_trip["budget"]
        s = TripRequestSerializer(data=sample_trip)
        assert not s.is_valid()
        assert "budget" in s.errors

    def test_missing_travelers(self, sample_trip):
        del sample_trip["travelers"]
        s = TripRequestSerializer(data=sample_trip)
        assert not s.is_valid()
        assert "travelers" in s.errors

    def test_optional_fields_default(self):
        data = {
            "destination": "Tokyo",
            "start_date": _future(30),
            "end_date": _future(32),
            "travelers": {"adults": 1},
            "budget": {"currency": "JPY", "total_budget": 100000, "comfort_level": "budget"},
        }
        s = TripRequestSerializer(data=data)
        assert s.is_valid(), s.errors
        validated = s.validated_data
        assert validated["daily_start_time"] == time(9, 0)
        assert validated["daily_end_time"] == time(20, 0)

    def test_long_destination_accepted(self):
        data = {
            "destination": "A" * 500,
            "start_date": _future(30),
            "end_date": _future(32),
            "travelers": {"adults": 1},
            "budget": {"currency": "USD", "total_budget": 500, "comfort_level": "budget"},
        }
        s = TripRequestSerializer(data=data)
        assert s.is_valid(), s.errors

    def test_destination_too_long(self):
        data = {
            "destination": "A" * 501,
            "start_date": _future(30),
            "end_date": _future(32),
            "travelers": {"adults": 1},
            "budget": {"currency": "USD", "total_budget": 500, "comfort_level": "budget"},
        }
        s = TripRequestSerializer(data=data)
        assert not s.is_valid()

    def test_unknown_location_valid(self, unknown_location_trip):
        s = TripRequestSerializer(data=unknown_location_trip)
        assert s.is_valid(), s.errors

    def test_multi_city_valid(self, multi_city_trip):
        s = TripRequestSerializer(data=multi_city_trip)
        assert s.is_valid(), s.errors


class TestTravelersSerializer:
    def test_valid(self):
        s = TravelersSerializer(data={"adults": 2, "children": 1})
        assert s.is_valid()

    def test_zero_adults_invalid(self):
        s = TravelersSerializer(data={"adults": 0, "children": 0})
        assert not s.is_valid()

    def test_negative_children_invalid(self):
        s = TravelersSerializer(data={"adults": 1, "children": -1})
        assert not s.is_valid()


class TestBudgetPreferencesSerializer:
    def test_valid(self):
        s = BudgetPreferencesSerializer(data={"currency": "USD", "total_budget": 1000, "comfort_level": "luxury"})
        assert s.is_valid()

    def test_invalid_comfort_level(self):
        s = BudgetPreferencesSerializer(data={"currency": "USD", "total_budget": 1000, "comfort_level": "ultra"})
        assert not s.is_valid()

    def test_invalid_currency_length(self):
        s = BudgetPreferencesSerializer(data={"currency": "US", "total_budget": 100, "comfort_level": "budget"})
        assert not s.is_valid()


class TestActivityPreferencesSerializer:
    def test_valid_pace_choices(self):
        for pace in ["slow", "moderate", "fast"]:
            s = ActivityPreferencesSerializer(data={"pace": pace})
            assert s.is_valid(), f"Pace '{pace}' should be valid"

    def test_invalid_pace(self):
        s = ActivityPreferencesSerializer(data={"pace": "extreme"})
        assert not s.is_valid()
