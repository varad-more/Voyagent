"""
Tests for database models: Itinerary, AgentTrace, ExternalCache.
"""
import pytest
from datetime import timedelta
from django.utils import timezone

from trip_planner.models import Itinerary, ItineraryStatus, AgentTrace, ExternalCache


pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Itinerary model
# ---------------------------------------------------------------------------

class TestItinerary:
    def test_create_itinerary(self, sample_trip):
        itinerary = Itinerary.objects.create(
            request_json=sample_trip,
            status=ItineraryStatus.PENDING,
        )
        assert itinerary.id is not None
        assert itinerary.status == ItineraryStatus.PENDING
        assert itinerary.result_json is None
        assert itinerary.error_message is None

    def test_destination_property(self, sample_trip):
        itinerary = Itinerary.objects.create(request_json=sample_trip)
        assert itinerary.destination == "Paris, France"

    def test_destination_property_missing(self):
        itinerary = Itinerary.objects.create(request_json={})
        assert itinerary.destination == ""

    def test_mark_processing(self, sample_trip):
        itinerary = Itinerary.objects.create(request_json=sample_trip)
        itinerary.mark_processing()
        itinerary.refresh_from_db()
        assert itinerary.status == ItineraryStatus.PROCESSING

    def test_mark_completed(self, sample_trip):
        itinerary = Itinerary.objects.create(
            request_json=sample_trip,
            status=ItineraryStatus.PROCESSING,
        )
        result = {"days": [], "summary": "Done"}
        itinerary.mark_completed(result)
        itinerary.refresh_from_db()
        assert itinerary.status == ItineraryStatus.COMPLETED
        assert itinerary.result_json == result

    def test_mark_failed(self, sample_trip):
        itinerary = Itinerary.objects.create(
            request_json=sample_trip,
            status=ItineraryStatus.PROCESSING,
        )
        itinerary.mark_failed("API timeout")
        itinerary.refresh_from_db()
        assert itinerary.status == ItineraryStatus.FAILED
        assert itinerary.error_message == "API timeout"

    def test_str_representation(self, sample_trip):
        itinerary = Itinerary.objects.create(request_json=sample_trip)
        assert "Paris, France" in str(itinerary)
        assert "pending" in str(itinerary)

    def test_ordering_newest_first(self, sample_trip):
        it1 = Itinerary.objects.create(request_json=sample_trip)
        it2 = Itinerary.objects.create(request_json=sample_trip)
        results = list(Itinerary.objects.all())
        assert results[0].id == it2.id  # newest first


# ---------------------------------------------------------------------------
# AgentTrace model
# ---------------------------------------------------------------------------

class TestAgentTrace:
    def test_create_trace(self, sample_trip):
        itinerary = Itinerary.objects.create(request_json=sample_trip)
        trace = AgentTrace.create_trace(
            itinerary=itinerary,
            agent_name="planner",
            step_name="final",
            input_data={"trip": sample_trip},
            output_data={"summary": "Done"},
            issues="minor warning",
        )
        assert trace.id is not None
        assert trace.agent_name == "planner"
        assert trace.step_name == "final"
        assert trace.issues == "minor warning"

    def test_trace_cascade_delete(self, sample_trip):
        itinerary = Itinerary.objects.create(request_json=sample_trip)
        AgentTrace.create_trace(itinerary, "test", "step1")
        AgentTrace.create_trace(itinerary, "test", "step2")
        assert AgentTrace.objects.filter(itinerary=itinerary).count() == 2
        itinerary.delete()
        assert AgentTrace.objects.count() == 0

    def test_str_representation(self, sample_trip):
        itinerary = Itinerary.objects.create(request_json=sample_trip)
        trace = AgentTrace.create_trace(itinerary, "weather", "draft_1")
        assert "weather" in str(trace)
        assert "draft_1" in str(trace)


# ---------------------------------------------------------------------------
# ExternalCache model
# ---------------------------------------------------------------------------

class TestExternalCache:
    def test_set_and_get_valid(self):
        ExternalCache.set_cache("test_key", "weather", {"temp": 25}, ttl_seconds=3600)
        result = ExternalCache.get_valid("test_key")
        assert result == {"temp": 25}

    def test_get_expired_returns_none(self):
        ExternalCache.set_cache("expired_key", "weather", {"temp": 10}, ttl_seconds=1)
        # Manually expire it
        entry = ExternalCache.objects.get(cache_key="expired_key")
        entry.expires_at = timezone.now() - timedelta(seconds=10)
        entry.save()
        assert ExternalCache.get_valid("expired_key") is None

    def test_get_nonexistent_returns_none(self):
        assert ExternalCache.get_valid("does_not_exist") is None

    def test_update_existing_cache(self):
        ExternalCache.set_cache("update_key", "places", {"v": 1}, ttl_seconds=3600)
        ExternalCache.set_cache("update_key", "places", {"v": 2}, ttl_seconds=3600)
        assert ExternalCache.get_valid("update_key") == {"v": 2}
        assert ExternalCache.objects.filter(cache_key="update_key").count() == 1

    def test_is_expired_property(self):
        ExternalCache.set_cache("prop_key", "test", {}, ttl_seconds=3600)
        entry = ExternalCache.objects.get(cache_key="prop_key")
        assert not entry.is_expired

        entry.expires_at = timezone.now() - timedelta(seconds=1)
        entry.save()
        assert entry.is_expired

    def test_cleanup_expired(self):
        ExternalCache.set_cache("keep", "test", {}, ttl_seconds=3600)
        ExternalCache.set_cache("remove", "test", {}, ttl_seconds=1)
        entry = ExternalCache.objects.get(cache_key="remove")
        entry.expires_at = timezone.now() - timedelta(seconds=10)
        entry.save()

        deleted_count, _ = ExternalCache.cleanup_expired()
        assert deleted_count == 1
        assert ExternalCache.objects.filter(cache_key="keep").exists()
        assert not ExternalCache.objects.filter(cache_key="remove").exists()

    def test_str_representation(self):
        ExternalCache.set_cache("str_test_key", "weather", {}, ttl_seconds=3600)
        entry = ExternalCache.objects.get(cache_key="str_test_key")
        assert "weather" in str(entry)
