"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";
import { ItineraryResponse } from "@/lib/types";
import { TripRequest } from "@/lib/validation";
import { ItineraryResult } from "@/components/ItineraryResult";
import { TripForm } from "@/components/TripForm";

export default function HomePage() {
  const [itinerary, setItinerary] = useState<ItineraryResponse | null>(null);
  const mutation = useMutation({
    mutationFn: async (payload: TripRequest) => {
      return apiFetch<ItineraryResponse>("/api/itineraries/generate", {
        method: "POST",
        body: JSON.stringify(payload),
      });
    },
    onSuccess: (data) => {
      setItinerary(data);
    },
  });

  return (
    <main className="mx-auto flex w-full max-w-6xl flex-col gap-8 px-6 py-10">
      <header className="space-y-3">
        <p className="text-sm uppercase tracking-[0.4em] text-emerald-300">
          Agentic Gemini Trip Planner
        </p>
        <h1 className="text-4xl font-semibold text-white md:text-5xl">
          Build a foolproof, weather-aware itinerary in minutes.
        </h1>
        <p className="max-w-2xl text-sm text-slate-300">
          Our multi-agent planner validates schedules, ranks attractions, and designs realistic
          day-by-day plans with buffers, meals, and budget safeguards.
        </p>
      </header>

      <TripForm onSubmit={(payload) => mutation.mutate(payload)} isLoading={mutation.isPending} />

      {mutation.error ? (
        <div className="rounded-2xl border border-rose-400/40 bg-rose-500/10 p-4 text-sm text-rose-200">
          {(mutation.error as Error).message}
        </div>
      ) : null}

      {itinerary ? <ItineraryResult itinerary={itinerary} /> : null}
    </main>
  );
}
