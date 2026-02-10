"""
API endpoint tests using Django REST Framework test client.
"""
import pytest
import uuid
from unittest.mock import patch
from datetime import date, timedelta

from rest_framework.test import APIClient

from trip_planner.models import Itinerary, ItineraryStatus


pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client():
    return APIClient()


def _future(days=30):
    return (date.today() + timedelta(days=days)).isoformat()


# ---------------------------------------------------------------------------
# POST /api/itineraries/ — Create
# ---------------------------------------------------------------------------

class TestItineraryCreate:
    def test_create_success(self, api_client, sample_trip):
        resp = api_client.post("/api/itineraries/", sample_trip, format="json")
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "queued"
        assert "id" in data

    def test_create_validation_error(self, api_client):
        resp = api_client.post("/api/itineraries/", {}, format="json")
        assert resp.status_code == 400
        assert "error" in resp.json()

    def test_create_end_before_start(self, api_client, sample_trip):
        sample_trip["start_date"] = _future(35)
        sample_trip["end_date"] = _future(30)
        resp = api_client.post("/api/itineraries/", sample_trip, format="json")
        assert resp.status_code == 400

    def test_create_unknown_location(self, api_client, unknown_location_trip):
        resp = api_client.post("/api/itineraries/", unknown_location_trip, format="json")
        assert resp.status_code == 201

    def test_create_multi_city(self, api_client, multi_city_trip):
        resp = api_client.post("/api/itineraries/", multi_city_trip, format="json")
        assert resp.status_code == 201


# ---------------------------------------------------------------------------
# POST /api/itineraries/generate — Synchronous generation
# ---------------------------------------------------------------------------

class TestItineraryGenerate:
    @patch("trip_planner.api.views.itineraries.generate_itinerary")
    def test_generate_success(self, mock_gen, api_client, sample_trip):
        mock_gen.return_value = {
            "itinerary_id": "test-id",
            "summary": "Trip to Paris",
            "days": [],
            "weather": {},
            "attractions": [],
            "packing_list": [],
            "budget": {},
            "validation": [],
            "warnings": [],
            "travel_options": [],
            "transport_analysis": None,
            "generated_at": "2026-04-01T00:00:00Z"
        }

        resp = api_client.post("/api/itineraries/generate", sample_trip, format="json")
        assert resp.status_code == 200
        data = resp.json()
        assert "itinerary_id" in data
        assert data["summary"] == "Trip to Paris"

    @patch("trip_planner.api.views.itineraries.generate_itinerary")
    def test_generate_gemini_error(self, mock_gen, api_client, sample_trip):
        from trip_planner.core.exceptions import GeminiError
        mock_gen.side_effect = GeminiError("No API key")

        resp = api_client.post("/api/itineraries/generate", sample_trip, format="json")
        assert resp.status_code == 503
        assert "gemini" in resp.json().get("error", "").lower()

    @patch("trip_planner.api.views.itineraries.generate_itinerary")
    def test_generate_internal_error(self, mock_gen, api_client, sample_trip):
        mock_gen.side_effect = RuntimeError("Unexpected")

        resp = api_client.post("/api/itineraries/generate", sample_trip, format="json")
        assert resp.status_code == 500

    def test_generate_validation_error(self, api_client):
        resp = api_client.post("/api/itineraries/generate", {"destination": "X"}, format="json")
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# GET /api/itineraries/<id>/ — Detail
# ---------------------------------------------------------------------------

class TestItineraryDetail:
    def test_get_existing(self, api_client, sample_trip):
        it = Itinerary.objects.create(request_json=sample_trip)
        resp = api_client.get(f"/api/itineraries/{it.id}/")
        assert resp.status_code == 200
        assert resp.json()["id"] == str(it.id)

    def test_get_nonexistent(self, api_client):
        fake_id = uuid.uuid4()
        resp = api_client.get(f"/api/itineraries/{fake_id}/")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# PATCH /api/itineraries/<id>/ — Update result
# ---------------------------------------------------------------------------

class TestItineraryPatch:
    def test_patch_result(self, api_client, sample_trip):
        it = Itinerary.objects.create(request_json=sample_trip, status=ItineraryStatus.COMPLETED)
        new_result = {"days": [{"date": "2026-04-01", "schedule": []}]}
        resp = api_client.patch(f"/api/itineraries/{it.id}/", {"result": new_result}, format="json")
        assert resp.status_code == 200
        it.refresh_from_db()
        assert it.result_json == new_result


# ---------------------------------------------------------------------------
# GET /api/itineraries/<id>/ics — ICS download
# ---------------------------------------------------------------------------

class TestItineraryICS:
    def test_ics_download(self, api_client, sample_trip):
        result = {
            "itinerary_id": "test-ics",
            "days": [{
                "date": "2026-04-01",
                "schedule": [{
                    "start_time": "09:00", "end_time": "11:00",
                    "title": "Visit", "location": "Place", "description": "Do stuff"
                }]
            }]
        }
        it = Itinerary.objects.create(
            request_json=sample_trip,
            result_json=result,
            status=ItineraryStatus.COMPLETED,
        )
        resp = api_client.get(f"/api/itineraries/{it.id}/ics")
        assert resp.status_code == 200
        assert resp["Content-Type"] == "text/calendar"
        content = resp.content.decode()
        assert "BEGIN:VCALENDAR" in content

    def test_ics_no_result(self, api_client, sample_trip):
        it = Itinerary.objects.create(request_json=sample_trip)
        resp = api_client.get(f"/api/itineraries/{it.id}/ics")
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# GET /api/places/autocomplete — Places proxy
# ---------------------------------------------------------------------------

class TestPlacesAutocomplete:
    def test_stub_predictions(self, api_client):
        resp = api_client.get("/api/places/autocomplete", {"q": "Paris"})
        assert resp.status_code == 200
        data = resp.json()
        assert "predictions" in data
        assert len(data["predictions"]) > 0

    def test_short_query(self, api_client):
        resp = api_client.get("/api/places/autocomplete", {"q": "P"})
        assert resp.status_code == 200
        assert resp.json()["predictions"] == []

    def test_empty_query(self, api_client):
        resp = api_client.get("/api/places/autocomplete")
        assert resp.status_code == 200
        assert resp.json()["predictions"] == []


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

class TestHealthCheck:
    def test_health_endpoint(self, api_client):
        resp = api_client.get("/health")
        assert resp.status_code == 200
