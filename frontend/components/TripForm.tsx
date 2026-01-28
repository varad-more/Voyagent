"use client";

import { useState } from "react";

import { tripRequestSchema, TripRequest } from "@/lib/validation";

type TripFormProps = {
  onSubmit: (payload: TripRequest) => void;
  isLoading: boolean;
};

const defaultValues = {
  destination: "",
  start_date: "",
  end_date: "",
  adults: 2,
  children: 0,
  origin_location: "",
  cuisines: "",
  dietary_restrictions: "",
  avoid_ingredients: "",
  interests: "",
  pace: "moderate",
  lodging_type: "any",
  max_distance_km_from_center: 5,
  currency: "USD",
  total_budget: 1500,
  comfort_level: "midrange",
  daily_start_time: "09:00:00",
  daily_end_time: "20:00:00",
  notes: "",
};

export function TripForm({ onSubmit, isLoading }: TripFormProps) {
  const [values, setValues] = useState(defaultValues);
  const [error, setError] = useState<string | null>(null);

  const updateField = (field: keyof typeof defaultValues, value: string | number) => {
    setValues((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);

    const payload: TripRequest = {
      destination: values.destination,
      start_date: values.start_date,
      end_date: values.end_date,
      travelers: { adults: Number(values.adults), children: Number(values.children) },
      origin_location: values.origin_location || null,
      food_preferences: {
        cuisines: values.cuisines
          .split(",")
          .map((item) => item.trim())
          .filter(Boolean),
        dietary_restrictions: values.dietary_restrictions
          .split(",")
          .map((item) => item.trim())
          .filter(Boolean),
        avoid_ingredients: values.avoid_ingredients
          .split(",")
          .map((item) => item.trim())
          .filter(Boolean),
      },
      activity_preferences: {
        interests: values.interests
          .split(",")
          .map((item) => item.trim())
          .filter(Boolean),
        pace: values.pace as TripRequest["activity_preferences"]["pace"],
        accessibility_needs: [],
      },
      lodging_preferences: {
        lodging_type: values.lodging_type as TripRequest["lodging_preferences"]["lodging_type"],
        max_distance_km_from_center: Number(values.max_distance_km_from_center),
      },
      budget: {
        currency: values.currency.toUpperCase(),
        total_budget: Number(values.total_budget),
        comfort_level: values.comfort_level as TripRequest["budget"]["comfort_level"],
      },
      daily_start_time: values.daily_start_time,
      daily_end_time: values.daily_end_time,
      notes: values.notes || null,
    };

    const result = tripRequestSchema.safeParse(payload);
    if (!result.success) {
      setError(result.error.issues[0]?.message ?? "Invalid form data");
      return;
    }
    onSubmit(result.data);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6 rounded-3xl bg-slate-900/60 p-6 shadow-xl">
      <div>
        <h2 className="text-2xl font-semibold text-white">Plan your trip</h2>
        <p className="text-sm text-slate-300">
          Get a timed itinerary with weather contingencies, food, budget, and packing list.
        </p>
      </div>
      {error ? (
        <div className="rounded-xl border border-rose-400/50 bg-rose-500/10 p-3 text-sm text-rose-200">
          {error}
        </div>
      ) : null}
      <div className="grid gap-4 md:grid-cols-2">
        <label className="flex flex-col gap-2 text-sm">
          Destination
          <input
            className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2"
            value={values.destination}
            onChange={(event) => updateField("destination", event.target.value)}
            placeholder="Tokyo, Japan"
            required
          />
        </label>
        <label className="flex flex-col gap-2 text-sm">
          Origin (optional)
          <input
            className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2"
            value={values.origin_location}
            onChange={(event) => updateField("origin_location", event.target.value)}
            placeholder="San Francisco, CA"
          />
        </label>
        <label className="flex flex-col gap-2 text-sm">
          Start date
          <input
            type="date"
            className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2"
            value={values.start_date}
            onChange={(event) => updateField("start_date", event.target.value)}
            required
          />
        </label>
        <label className="flex flex-col gap-2 text-sm">
          End date
          <input
            type="date"
            className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2"
            value={values.end_date}
            onChange={(event) => updateField("end_date", event.target.value)}
            required
          />
        </label>
        <label className="flex flex-col gap-2 text-sm">
          Adults
          <input
            type="number"
            min={1}
            className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2"
            value={values.adults}
            onChange={(event) => updateField("adults", Number(event.target.value))}
          />
        </label>
        <label className="flex flex-col gap-2 text-sm">
          Children
          <input
            type="number"
            min={0}
            className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2"
            value={values.children}
            onChange={(event) => updateField("children", Number(event.target.value))}
          />
        </label>
        <label className="flex flex-col gap-2 text-sm">
          Interests (comma-separated)
          <input
            className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2"
            value={values.interests}
            onChange={(event) => updateField("interests", event.target.value)}
            placeholder="food, museums, nightlife"
          />
        </label>
        <label className="flex flex-col gap-2 text-sm">
          Pace
          <select
            className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2"
            value={values.pace}
            onChange={(event) => updateField("pace", event.target.value)}
          >
            <option value="slow">Slow</option>
            <option value="moderate">Moderate</option>
            <option value="fast">Fast</option>
          </select>
        </label>
        <label className="flex flex-col gap-2 text-sm">
          Cuisines
          <input
            className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2"
            value={values.cuisines}
            onChange={(event) => updateField("cuisines", event.target.value)}
            placeholder="sushi, tapas"
          />
        </label>
        <label className="flex flex-col gap-2 text-sm">
          Dietary restrictions
          <input
            className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2"
            value={values.dietary_restrictions}
            onChange={(event) => updateField("dietary_restrictions", event.target.value)}
            placeholder="vegetarian, gluten-free"
          />
        </label>
        <label className="flex flex-col gap-2 text-sm">
          Avoid ingredients
          <input
            className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2"
            value={values.avoid_ingredients}
            onChange={(event) => updateField("avoid_ingredients", event.target.value)}
            placeholder="peanuts, shellfish"
          />
        </label>
        <label className="flex flex-col gap-2 text-sm">
          Budget (total)
          <input
            type="number"
            min={0}
            className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2"
            value={values.total_budget}
            onChange={(event) => updateField("total_budget", Number(event.target.value))}
          />
        </label>
        <label className="flex flex-col gap-2 text-sm">
          Currency
          <input
            className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2"
            value={values.currency}
            onChange={(event) => updateField("currency", event.target.value.toUpperCase())}
            placeholder="USD"
          />
        </label>
        <label className="flex flex-col gap-2 text-sm">
          Comfort level
          <select
            className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2"
            value={values.comfort_level}
            onChange={(event) => updateField("comfort_level", event.target.value)}
          >
            <option value="budget">Budget</option>
            <option value="midrange">Midrange</option>
            <option value="luxury">Luxury</option>
          </select>
        </label>
        <label className="flex flex-col gap-2 text-sm">
          Lodging type
          <select
            className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2"
            value={values.lodging_type}
            onChange={(event) => updateField("lodging_type", event.target.value)}
          >
            <option value="any">Any</option>
            <option value="hotel">Hotel</option>
            <option value="hostel">Hostel</option>
            <option value="apartment">Apartment</option>
            <option value="boutique">Boutique</option>
          </select>
        </label>
        <label className="flex flex-col gap-2 text-sm">
          Max distance from center (km)
          <input
            type="number"
            min={0}
            className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2"
            value={values.max_distance_km_from_center}
            onChange={(event) => updateField("max_distance_km_from_center", Number(event.target.value))}
          />
        </label>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <label className="flex flex-col gap-2 text-sm">
          Daily start time
          <input
            type="time"
            className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2"
            value={values.daily_start_time}
            onChange={(event) => updateField("daily_start_time", event.target.value)}
          />
        </label>
        <label className="flex flex-col gap-2 text-sm">
          Daily end time
          <input
            type="time"
            className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2"
            value={values.daily_end_time}
            onChange={(event) => updateField("daily_end_time", event.target.value)}
          />
        </label>
        <label className="flex flex-col gap-2 text-sm md:col-span-2">
          Notes
          <textarea
            className="min-h-[90px] rounded-lg border border-slate-700 bg-slate-950 px-3 py-2"
            value={values.notes}
            onChange={(event) => updateField("notes", event.target.value)}
            placeholder="Any must-dos, pace constraints, celebrations..."
          />
        </label>
      </div>
      <button
        type="submit"
        disabled={isLoading}
        className="w-full rounded-xl bg-emerald-500 px-4 py-3 text-base font-semibold text-slate-950 transition hover:bg-emerald-400 disabled:cursor-not-allowed disabled:bg-slate-700"
      >
        {isLoading ? "Planning..." : "Generate itinerary"}
      </button>
    </form>
  );
}
