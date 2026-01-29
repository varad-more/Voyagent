from __future__ import annotations

import datetime as dt
from typing import Literal

from pydantic import BaseModel, Field
from pydantic.config import ConfigDict


class StrictBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Travelers(StrictBaseModel):
    adults: int = Field(ge=1)
    children: int = Field(ge=0, default=0)


class FoodPreferences(StrictBaseModel):
    cuisines: list[str] = Field(default_factory=list)
    dietary_restrictions: list[str] = Field(default_factory=list)
    avoid_ingredients: list[str] = Field(default_factory=list)


class ActivityPreferences(StrictBaseModel):
    interests: list[str] = Field(default_factory=list)
    pace: Literal["slow", "moderate", "fast"] = "moderate"
    accessibility_needs: list[str] = Field(default_factory=list)


class LodgingPreferences(StrictBaseModel):
    lodging_type: Literal["hotel", "hostel", "apartment", "boutique", "any"] = "any"
    max_distance_km_from_center: float = Field(default=5.0, ge=0)


class BudgetPreferences(StrictBaseModel):
    currency: str = Field(default="USD", min_length=3, max_length=3)
    total_budget: float = Field(ge=0)
    comfort_level: Literal["budget", "midrange", "luxury"] = "midrange"


class TripRequest(StrictBaseModel):
    destination: str
    start_date: dt.date
    end_date: dt.date
    travelers: Travelers
    origin_location: str | None = None
    food_preferences: FoodPreferences = Field(default_factory=FoodPreferences)
    activity_preferences: ActivityPreferences = Field(default_factory=ActivityPreferences)
    lodging_preferences: LodgingPreferences = Field(default_factory=LodgingPreferences)
    budget: BudgetPreferences
    daily_start_time: dt.time = Field(default=dt.time(hour=9))
    daily_end_time: dt.time = Field(default=dt.time(hour=20))
    notes: str | None = None


class WeatherDay(StrictBaseModel):
    date: dt.date
    high_c: float
    low_c: float
    precipitation_chance: float = Field(ge=0, le=1)
    summary: str


class WeatherSummary(StrictBaseModel):
    forecast_source: str
    overview: str
    risks: list[str] = Field(default_factory=list)
    daily: list[WeatherDay] = Field(default_factory=list)


class MicroActivity(StrictBaseModel):
    name: str
    reason: str
    distance_minutes: int = Field(ge=0)


class ScheduleBlock(StrictBaseModel):
    start_time: dt.time
    end_time: dt.time
    title: str
    location: str
    description: str
    block_type: Literal["activity", "meal", "travel", "rest", "buffer"]
    travel_time_mins: int = Field(ge=0, default=0)
    buffer_mins: int = Field(ge=0, default=0)
    micro_activities: list[MicroActivity] = Field(default_factory=list)


class MealPlan(StrictBaseModel):
    time: dt.time
    name: str
    cuisine: str
    dietary_fit: list[str] = Field(default_factory=list)
    location: str
    reservation_needed: bool = False
    estimated_cost: float = Field(ge=0, default=0)


class DayPlan(StrictBaseModel):
    date: dt.date
    title: str
    weather_summary: str
    contingencies: list[str] = Field(default_factory=list)
    schedule: list[ScheduleBlock] = Field(default_factory=list)
    meals: list[MealPlan] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class Attraction(StrictBaseModel):
    name: str
    reason: str
    score: float = Field(ge=0, le=1)
    distance_km: float = Field(ge=0)
    categories: list[str] = Field(default_factory=list)
    address: str | None = None


class BudgetItem(StrictBaseModel):
    category: str
    estimated_cost: float = Field(ge=0)
    notes: str | None = None


class BudgetPlan(StrictBaseModel):
    currency: str
    total_budget: float = Field(ge=0)
    estimated_total: float = Field(ge=0)
    breakdown: list[BudgetItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    downgrade_plan: list[str] = Field(default_factory=list)


class ValidationResult(StrictBaseModel):
    check: str
    status: Literal["pass", "warn", "fail"]
    details: str


class TransportOption(StrictBaseModel):
    mode: Literal["public_transit", "private_driver", "rental_car", "taxi", "rideshare", "walking"]
    description: str
    cost_estimate: str
    duration_estimate: str
    fuel_cost_estimate: str | None = None
    misc_costs: list[str] = Field(default_factory=list)
    pros: list[str] = Field(default_factory=list)
    cons: list[str] = Field(default_factory=list)


class TransportAnalysis(StrictBaseModel):
    options: list[TransportOption] = Field(default_factory=list)
    recommended_mode: str
    reasoning: str


class TravelOption(StrictBaseModel):
    type: Literal["car", "hotel", "flight"]
    name: str
    provider: str
    price_estimate: str
    details: str
    booking_url: str | None = None
    rating: float | None = None
    features: list[str] = Field(default_factory=list)


class ItineraryResponse(StrictBaseModel):
    itinerary_id: int
    summary: str
    days: list[DayPlan]
    weather: WeatherSummary
    attractions: list[Attraction]
    packing_list: list[str]
    budget: BudgetPlan
    validation: list[ValidationResult]
    warnings: list[str] = Field(default_factory=list)
    travel_options: list[TravelOption] = Field(default_factory=list)
    transport_analysis: TransportAnalysis | None = None
    generated_at: dt.datetime


class ItineraryRecord(StrictBaseModel):
    id: int
    status: str
    request: TripRequest
    result: ItineraryResponse | None = None
    error_message: str | None = None
    created_at: dt.datetime
    updated_at: dt.datetime
