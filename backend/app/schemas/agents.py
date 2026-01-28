from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, Field
from pydantic.config import ConfigDict

from app.schemas.itinerary import (
    Attraction,
    BudgetPlan,
    DayPlan,
    MealPlan,
    ScheduleBlock,
    ValidationResult,
    WeatherSummary,
)


class StrictBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=True)


class DaySkeleton(StrictBaseModel):
    date: dt.date
    theme: str
    must_do: list[str] = Field(default_factory=list)
    optional_stops: list[str] = Field(default_factory=list)


class PlannerOutput(StrictBaseModel):
    summary: str
    days: list[DaySkeleton]


class WeatherAgentOutput(StrictBaseModel):
    weather: WeatherSummary
    adjustments: list[str] = Field(default_factory=list)


class AttractionsAgentOutput(StrictBaseModel):
    attractions: list[Attraction]


class SchedulerDay(StrictBaseModel):
    date: dt.date
    weather_summary: str
    schedule: list[ScheduleBlock] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class SchedulerOutput(StrictBaseModel):
    days: list[SchedulerDay]


class FoodDay(StrictBaseModel):
    date: dt.date
    meals: list[MealPlan] = Field(default_factory=list)


class FoodOutput(StrictBaseModel):
    days: list[FoodDay]


class BudgetOutput(StrictBaseModel):
    budget: BudgetPlan


class ValidatorOutput(StrictBaseModel):
    validation: list[ValidationResult]
    warnings: list[str] = Field(default_factory=list)


class OrchestratorOutput(StrictBaseModel):
    summary: str
    days: list[DayPlan]
    weather: WeatherSummary
    attractions: list[Attraction]
    packing_list: list[str]
    budget: BudgetPlan
    validation: list[ValidationResult]
    warnings: list[str] = Field(default_factory=list)
