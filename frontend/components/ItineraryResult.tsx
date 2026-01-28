"use client";

import { apiBaseUrl } from "@/lib/api";
import { ItineraryResponse } from "@/lib/types";

type ItineraryResultProps = {
  itinerary: ItineraryResponse;
};

export function ItineraryResult({ itinerary }: ItineraryResultProps) {
  const icsLink = `${apiBaseUrl}/api/itineraries/${itinerary.itinerary_id}/ics`;

  return (
    <section className="space-y-6">
      <div className="rounded-3xl bg-slate-900/60 p-6 shadow-xl">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <h2 className="text-2xl font-semibold text-white">Itinerary summary</h2>
            <p className="text-slate-300">{itinerary.summary}</p>
          </div>
          <a
            href={icsLink}
            className="inline-flex items-center justify-center rounded-xl border border-emerald-400/40 px-4 py-2 text-sm font-semibold text-emerald-200 hover:border-emerald-300"
          >
            Download .ics
          </a>
        </div>
        {itinerary.warnings.length ? (
          <div className="mt-4 rounded-xl border border-amber-400/50 bg-amber-500/10 p-3 text-sm text-amber-200">
            <p className="font-semibold">Warnings</p>
            <ul className="list-disc pl-5">
              {itinerary.warnings.map((warning) => (
                <li key={warning}>{warning}</li>
              ))}
            </ul>
          </div>
        ) : null}
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="rounded-3xl bg-slate-900/60 p-6 shadow-xl lg:col-span-2">
          <h3 className="text-xl font-semibold text-white">Day-by-day plan</h3>
          <div className="mt-4 space-y-6">
            {itinerary.days.map((day) => (
              <div key={day.date} className="rounded-2xl border border-slate-800 bg-slate-950/40 p-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <p className="text-sm text-emerald-300">{day.date}</p>
                    <h4 className="text-lg font-semibold text-white">{day.title}</h4>
                  </div>
                  <span className="text-xs text-slate-400">{day.weather_summary}</span>
                </div>
                <ul className="mt-3 space-y-3">
                  {day.schedule.map((block) => (
                    <li key={`${day.date}-${block.title}-${block.start_time}`}>
                      <div className="flex flex-wrap items-center justify-between gap-2 text-sm">
                        <span className="font-semibold text-white">
                          {block.start_time} - {block.end_time}
                        </span>
                        <span className="text-xs uppercase text-slate-400">{block.block_type}</span>
                      </div>
                      <p className="text-sm text-slate-200">{block.title}</p>
                      <p className="text-xs text-slate-400">{block.location}</p>
                      <p className="text-xs text-slate-500">{block.description}</p>
                      {block.micro_activities.length ? (
                        <ul className="mt-2 list-disc pl-5 text-xs text-slate-400">
                          {block.micro_activities.map((micro) => (
                            <li key={micro.name}>
                              {micro.name} — {micro.reason}
                            </li>
                          ))}
                        </ul>
                      ) : null}
                    </li>
                  ))}
                </ul>
                {day.meals.length ? (
                  <div className="mt-4">
                    <p className="text-sm font-semibold text-white">Meals</p>
                    <ul className="mt-2 space-y-2 text-sm text-slate-300">
                      {day.meals.map((meal) => (
                        <li key={`${day.date}-${meal.name}-${meal.time}`}>
                          {meal.time} · {meal.name} ({meal.cuisine})
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null}
                {day.contingencies.length ? (
                  <div className="mt-4 text-xs text-amber-200">
                    Contingencies: {day.contingencies.join(", ")}
                  </div>
                ) : null}
              </div>
            ))}
          </div>
        </div>

        <div className="space-y-6">
          <div className="rounded-3xl bg-slate-900/60 p-6 shadow-xl">
            <h3 className="text-lg font-semibold text-white">Packing list</h3>
            <ul className="mt-3 list-disc pl-5 text-sm text-slate-300">
              {itinerary.packing_list.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>

          <div className="rounded-3xl bg-slate-900/60 p-6 shadow-xl">
            <h3 className="text-lg font-semibold text-white">Budget</h3>
            <p className="text-sm text-slate-300">
              Estimated {itinerary.budget.currency} {itinerary.budget.estimated_total.toFixed(0)} /{" "}
              {itinerary.budget.total_budget.toFixed(0)}
            </p>
            <ul className="mt-3 text-sm text-slate-300">
              {itinerary.budget.breakdown.map((item) => (
                <li key={item.category} className="flex justify-between">
                  <span>{item.category}</span>
                  <span>{item.estimated_cost.toFixed(0)}</span>
                </li>
              ))}
            </ul>
            {itinerary.budget.warnings.length ? (
              <div className="mt-3 text-xs text-amber-200">
                {itinerary.budget.warnings.join(" ")}
              </div>
            ) : null}
            {itinerary.budget.downgrade_plan.length ? (
              <div className="mt-3 text-xs text-slate-400">
                Downgrade plan: {itinerary.budget.downgrade_plan.join(" ")}
              </div>
            ) : null}
          </div>

          <div className="rounded-3xl bg-slate-900/60 p-6 shadow-xl">
            <h3 className="text-lg font-semibold text-white">Top attractions</h3>
            <ul className="mt-3 space-y-2 text-sm text-slate-300">
              {itinerary.attractions.map((attraction) => (
                <li key={attraction.name}>
                  <p className="font-semibold text-white">{attraction.name}</p>
                  <p className="text-xs text-slate-400">{attraction.reason}</p>
                </li>
              ))}
            </ul>
          </div>

          <div className="rounded-3xl bg-slate-900/60 p-6 shadow-xl">
            <h3 className="text-lg font-semibold text-white">Validation</h3>
            <ul className="mt-3 space-y-2 text-sm text-slate-300">
              {itinerary.validation.map((check) => (
                <li key={check.check}>
                  <span className="font-semibold">{check.status.toUpperCase()}</span> —{" "}
                  {check.details}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
}
