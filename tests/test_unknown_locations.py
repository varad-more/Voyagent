"""
Tests for handling unknown, obscure, and non-standard locations.

Validates that the system can:
1. Accept any destination string without crashing
2. Generate valid stub/AI output for obscure places
3. Handle non-English destination names
4. Handle multi-city routes
5. Gracefully degrade when external APIs have no data for a location
"""
import pytest
from datetime import date, timedelta
from unittest.mock import patch

from trip_planner.agents.planner import PlannerAgent
from trip_planner.agents.weather import WeatherAgent
from trip_planner.agents.attractions import AttractionsAgent
from trip_planner.agents.scheduler import SchedulerAgent
from trip_planner.agents.food import FoodAgent
from trip_planner.agents.budget import BudgetAgent
from trip_planner.agents.validator import ValidatorAgent
from trip_planner.agents.research import ResearchAgent


pytestmark = pytest.mark.django_db


def _future(days=60):
    return (date.today() + timedelta(days=days)).isoformat()


# ---------------------------------------------------------------------------
# Test data: Unusual destinations
# ---------------------------------------------------------------------------

OBSCURE_DESTINATIONS = [
    "Tórshavn, Faroe Islands",
    "Longyearbyen, Svalbard",
    "Nauru",
    "Timbuktu, Mali",
    "Yakutsk, Russia",
    "Upernavik, Greenland",
    "Tristan da Cunha",
    "Pitcairn Islands",
]

NON_ENGLISH_DESTINATIONS = [
    "東京",           # Tokyo in Japanese
    "Zürich",         # with umlaut
    "São Paulo",      # with tilde
    "مراكش",          # Marrakech in Arabic
    "Москва",         # Moscow in Russian
    "กรุงเทพมหานคร",  # Bangkok in Thai
]

MULTI_CITY_ROUTES = [
    "Tempe -> Grand Canyon -> Las Vegas",
    "Tokyo -> Kyoto -> Osaka",
    "Berlin, Munich, Vienna",
    "Rome → Florence → Venice",
]


def _make_trip(destination):
    """Create a minimal valid trip dict for the given destination."""
    return {
        "destination": destination,
        "start_date": _future(60),
        "end_date": _future(62),
        "travelers": {"adults": 1, "children": 0},
        "food_preferences": {"cuisines": [], "dietary_restrictions": [], "avoid_ingredients": []},
        "activity_preferences": {"interests": ["sightseeing"], "pace": "moderate", "accessibility_needs": []},
        "lodging_preferences": {"lodging_type": "any", "max_distance_km_from_center": 5.0},
        "budget": {"currency": "USD", "total_budget": 1000.0, "comfort_level": "midrange"},
        "daily_start_time": "09:00",
        "daily_end_time": "20:00",
    }


# ---------------------------------------------------------------------------
# PlannerAgent: all destinations produce valid stubs
# ---------------------------------------------------------------------------

class TestPlannerUnknownLocations:
    @pytest.mark.parametrize("dest", OBSCURE_DESTINATIONS)
    def test_obscure_destination_stub(self, dest, mock_gemini_unavailable):
        trip = _make_trip(dest)
        agent = PlannerAgent(gemini_client=mock_gemini_unavailable)
        result = agent.run(trip=trip)

        assert result.data is not None
        assert "days" in result.data
        assert len(result.data["days"]) == 3  # 3-day trip
        assert "summary" in result.data

    @pytest.mark.parametrize("dest", NON_ENGLISH_DESTINATIONS)
    def test_non_english_destination_stub(self, dest, mock_gemini_unavailable):
        trip = _make_trip(dest)
        agent = PlannerAgent(gemini_client=mock_gemini_unavailable)
        result = agent.run(trip=trip)

        assert result.data is not None
        assert len(result.data["days"]) == 3

    @pytest.mark.parametrize("dest", MULTI_CITY_ROUTES)
    def test_multi_city_route_stub(self, dest, mock_gemini_unavailable):
        trip = _make_trip(dest)
        agent = PlannerAgent(gemini_client=mock_gemini_unavailable)
        result = agent.run(trip=trip)

        assert result.data is not None
        assert len(result.data["days"]) == 3


# ---------------------------------------------------------------------------
# WeatherAgent: unknown locations don't crash
# ---------------------------------------------------------------------------

class TestWeatherUnknownLocations:
    @pytest.mark.parametrize("dest", OBSCURE_DESTINATIONS[:3])
    @patch("trip_planner.agents.weather.get_weather")
    def test_weather_stub_for_obscure(self, mock_weather, dest, mock_gemini_unavailable):
        mock_weather.return_value = {"daily": [], "forecast_source": "stub"}
        trip = _make_trip(dest)
        agent = WeatherAgent(gemini_client=mock_gemini_unavailable)
        result = agent.run(trip=trip)

        assert result.data is not None
        assert "weather" in result.data
        assert "adjustments" in result.data


# ---------------------------------------------------------------------------
# AttractionsAgent: unknown locations return valid output
# ---------------------------------------------------------------------------

class TestAttractionsUnknownLocations:
    @pytest.mark.parametrize("dest", OBSCURE_DESTINATIONS[:3])
    @patch("trip_planner.agents.attractions.get_attractions")
    def test_attractions_for_obscure(self, mock_places, dest, mock_gemini_unavailable):
        mock_places.return_value = {"attractions": [{"name": f"Scenic view near {dest}"}]}
        trip = _make_trip(dest)
        agent = AttractionsAgent(gemini_client=mock_gemini_unavailable)
        result = agent.run(trip=trip)

        assert "attractions" in result.data
        assert len(result.data["attractions"]) > 0


# ---------------------------------------------------------------------------
# Full stub pipeline: every agent works end-to-end for an obscure destination
# ---------------------------------------------------------------------------

class TestFullStubPipelineUnknownLocation:
    @patch("trip_planner.agents.weather.get_weather")
    @patch("trip_planner.agents.attractions.get_attractions")
    def test_full_stub_pipeline(self, mock_attractions, mock_weather, mock_gemini_unavailable):
        """Ensure all agents can produce valid output for Svalbard with no AI."""
        dest = "Longyearbyen, Svalbard"
        trip = _make_trip(dest)

        mock_weather.return_value = {
            "daily": [
                {"date": _future(60), "temp_high": -5, "temp_low": -15,
                 "precipitation_chance": 0.2}
            ],
            "forecast_source": "stub"
        }
        mock_attractions.return_value = {
            "attractions": [{"name": "Svalbard Global Seed Vault", "rating": 4.5}]
        }

        # 1. Planner
        planner = PlannerAgent(gemini_client=mock_gemini_unavailable)
        planner_result = planner.run(trip=trip)
        assert len(planner_result.data["days"]) == 3

        # 2. Weather
        weather_agent = WeatherAgent(gemini_client=mock_gemini_unavailable)
        weather_result = weather_agent.run(trip=trip)
        assert "weather" in weather_result.data

        # 3. Attractions
        attractions_agent = AttractionsAgent(gemini_client=mock_gemini_unavailable)
        attractions_result = attractions_agent.run(trip=trip)
        assert "attractions" in attractions_result.data

        # 4. Scheduler
        scheduler = SchedulerAgent(gemini_client=mock_gemini_unavailable)
        scheduler_result = scheduler.run(
            trip=trip,
            planner_output=planner_result.data,
            weather_summary="Cold and dark"
        )
        assert len(scheduler_result.data["days"]) == 3

        # 5. Food
        food_agent = FoodAgent(gemini_client=mock_gemini_unavailable)
        food_result = food_agent.run(trip=trip, scheduler_output=scheduler_result.data)
        assert len(food_result.data["days"]) == 3

        # 6. Budget
        budget_agent = BudgetAgent(gemini_client=mock_gemini_unavailable)
        budget_result = budget_agent.run(
            trip=trip,
            scheduler_output=scheduler_result.data,
            food_output=food_result.data,
        )
        assert "budget" in budget_result.data
        assert budget_result.data["budget"]["currency"] == "USD"

        # 7. Validator
        validator = ValidatorAgent()
        validator_result = validator.run(trip=trip, scheduler_output=scheduler_result.data)
        assert "validation" in validator_result.data

    @patch("trip_planner.agents.weather.get_weather")
    @patch("trip_planner.agents.attractions.get_attractions")
    def test_made_up_location_doesnt_crash(self, mock_attractions, mock_weather, mock_gemini_unavailable):
        """A completely fictitious location should still produce valid output."""
        dest = "Xyzzyville, Planet Zog"
        trip = _make_trip(dest)

        mock_weather.return_value = {"daily": [], "forecast_source": "stub"}
        mock_attractions.return_value = {"attractions": []}

        planner = PlannerAgent(gemini_client=mock_gemini_unavailable)
        planner_result = planner.run(trip=trip)
        assert planner_result.data is not None
        assert "Xyzzyville" in planner_result.data.get("summary", "") or "Planet Zog" in planner_result.data.get("summary", "")

        scheduler = SchedulerAgent(gemini_client=mock_gemini_unavailable)
        scheduler_result = scheduler.run(
            trip=trip,
            planner_output=planner_result.data,
            weather_summary="Unknown"
        )
        assert len(scheduler_result.data["days"]) == 3

        validator = ValidatorAgent()
        validator_result = validator.run(trip=trip, scheduler_output=scheduler_result.data)
        failures = [v for v in validator_result.data["validation"] if v["status"] == "fail"]
        assert len(failures) == 0  # stub schedule should be valid


# ---------------------------------------------------------------------------
# Research Agent: unknown locations
# ---------------------------------------------------------------------------

class TestResearchUnknownLocations:
    @patch("trip_planner.agents.research.get_hotels")
    @patch("trip_planner.agents.research.get_travel_time_minutes")
    def test_research_for_obscure_location(self, mock_travel, mock_hotels, mock_gemini_unavailable):
        mock_hotels.return_value = {"hotels": []}
        mock_travel.return_value = {"travel_time_minutes": 20}

        agent = ResearchAgent(gemini_client=mock_gemini_unavailable)
        trip = _make_trip("Tristan da Cunha")
        context = agent.conduct_research(trip)

        assert isinstance(context, str)
        assert "Research Report" in context

    @patch("trip_planner.agents.research.get_hotels")
    @patch("trip_planner.agents.research.get_travel_time_minutes")
    def test_travel_options_stub_for_unknown(self, mock_travel, mock_hotels, mock_gemini_unavailable):
        mock_hotels.return_value = {"hotels": []}
        mock_travel.return_value = {"travel_time_minutes": 20}

        agent = ResearchAgent(gemini_client=mock_gemini_unavailable)
        trip = _make_trip("Pitcairn Islands")
        options = agent.get_travel_options(trip)

        assert "booking_options" in options
        assert "transport_analysis" in options
        assert len(options["booking_options"]) > 0


# ---------------------------------------------------------------------------
# API: unknown location end-to-end
# ---------------------------------------------------------------------------

class TestAPIUnknownLocations:
    def test_create_itinerary_with_non_english_name(self):
        from rest_framework.test import APIClient
        client = APIClient()
        trip = _make_trip("東京")
        resp = client.post("/api/itineraries/", trip, format="json")
        assert resp.status_code == 201

    def test_create_itinerary_with_special_chars(self):
        from rest_framework.test import APIClient
        client = APIClient()
        trip = _make_trip("São Paulo, Brazil")
        resp = client.post("/api/itineraries/", trip, format="json")
        assert resp.status_code == 201

    def test_create_itinerary_with_arrow_notation(self):
        from rest_framework.test import APIClient
        client = APIClient()
        trip = _make_trip("Berlin -> Munich -> Vienna")
        resp = client.post("/api/itineraries/", trip, format="json")
        assert resp.status_code == 201
