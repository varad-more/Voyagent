"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";
import { ItineraryResponse } from "@/lib/types";
import { TripRequest } from "@/lib/validation";
import ItineraryResult from "@/components/ItineraryResult";
import { TripForm } from "@/components/TripForm";
import { DUMMY_ITINERARY } from "@/lib/dummyData";

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
    <div className="min-h-screen relative">
      {/* Floating travel icons */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden z-0">
        <div className="absolute top-[10%] left-[5%] text-4xl floating-icon opacity-20" style={{ animationDelay: "0s" }}>✈️</div>
        <div className="absolute top-[20%] right-[10%] text-3xl floating-icon opacity-15" style={{ animationDelay: "1s" }}>🏝️</div>
        <div className="absolute bottom-[30%] left-[8%] text-3xl floating-icon opacity-20" style={{ animationDelay: "2s" }}>🗺️</div>
        <div className="absolute top-[60%] right-[5%] text-4xl floating-icon opacity-15" style={{ animationDelay: "1.5s" }}>🌍</div>
        <div className="absolute bottom-[15%] right-[15%] text-3xl floating-icon opacity-20" style={{ animationDelay: "3s" }}>🎒</div>
        <div className="absolute top-[40%] left-[3%] text-3xl floating-icon opacity-15" style={{ animationDelay: "2.5s" }}>🏔️</div>
      </div>

      {/* Main content */}
      <main className="relative z-10 mx-auto max-w-4xl px-4 sm:px-6 py-12 md:py-16">
        {/* Hero Section */}
        <header className="text-center mb-12 md:mb-16 relative">
          {/* Glowing orb behind title */}
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 
                          bg-gradient-to-r from-blue-500/20 via-purple-500/20 to-pink-500/20 
                          rounded-full blur-3xl animate-glow -z-10" />

          {/* AI Badge */}
          <div className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full mb-8
                          bg-gradient-to-r from-blue-500/10 via-purple-500/10 to-pink-500/10
                          border border-purple-500/30 backdrop-blur-sm
                          animate-fadeIn shadow-lg shadow-purple-500/10">
            <span className="relative flex h-2.5 w-2.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-purple-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-gradient-to-r from-blue-400 to-purple-400"></span>
            </span>
            <span className="text-sm font-semibold bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 
                           bg-clip-text text-transparent tracking-wide">
              AI-Powered Trip Planning
            </span>
            <span className="text-lg">✨</span>
          </div>

          {/* Main heading */}
          <h1 className="text-5xl sm:text-6xl md:text-7xl font-bold mb-6 leading-tight tracking-tight">
            <span className="text-white">Discover Your</span>
            <br />
            <span className="hero-gradient">Dream Destination</span>
          </h1>

          {/* Subtitle */}
          <p className="text-lg md:text-xl text-slate-300 max-w-2xl mx-auto mb-10 leading-relaxed">
            Let AI craft your <span className="text-purple-400 font-medium">perfect itinerary</span> with
            real-time weather, smart scheduling, and personalized recommendations —
            all in <span className="text-blue-400 font-medium">minutes</span>.
          </p>

          {/* Feature cards */}
          <div className="flex flex-wrap justify-center gap-4 text-sm">
            {[
              { icon: "🌤️", text: "Weather-Aware", color: "from-yellow-500/20 to-orange-500/20", border: "border-orange-500/30" },
              { icon: "📍", text: "Smart Routing", color: "from-blue-500/20 to-cyan-500/20", border: "border-cyan-500/30" },
              { icon: "💰", text: "Budget Planning", color: "from-green-500/20 to-emerald-500/20", border: "border-emerald-500/30" },
              { icon: "✨", text: "AI Personalized", color: "from-purple-500/20 to-pink-500/20", border: "border-pink-500/30" },
            ].map((feature) => (
              <span
                key={feature.text}
                className={`inline-flex items-center gap-2.5 px-5 py-3 rounded-2xl
                           bg-gradient-to-br ${feature.color} 
                           border ${feature.border}
                           text-white font-medium
                           backdrop-blur-sm
                           hover:scale-105 transition-all duration-300
                           shadow-lg hover:shadow-xl cursor-default`}
              >
                <span className="text-xl">{feature.icon}</span>
                <span>{feature.text}</span>
              </span>
            ))}
          </div>
        </header>

        {/* Form Section */}
        {!itinerary && (
          <section className="relative">
            <TripForm
              onSubmit={(payload) => mutation.mutate(payload)}
              isLoading={mutation.isPending}
            />
            <div className="mt-6 text-center">
              <button
                onClick={() => setItinerary(DUMMY_ITINERARY)}
                className="text-sm font-medium text-slate-500 hover:text-purple-400 transition-colors flex items-center justify-center gap-2 mx-auto group"
              >
                <span>👀</span>
                <span className="group-hover:underline">Preview with Demo Data</span>
              </button>
            </div>
          </section>
        )}

        {/* Error Display */}
        {mutation.error && (
          <div className="mt-8 p-6 rounded-2xl bg-gradient-to-r from-rose-500/10 to-red-500/10 
                          border border-rose-500/30 animate-fadeIn backdrop-blur-sm">
            <div className="flex items-start gap-4">
              <div className="p-3 bg-rose-500/20 rounded-xl">
                <svg className="w-6 h-6 text-rose-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div>
                <h3 className="text-lg font-semibold text-rose-200 mb-1">Oops! Something went wrong</h3>
                <p className="text-rose-300/80 text-sm">{(mutation.error as Error).message}</p>
                <button
                  type="button"
                  onClick={() => mutation.reset()}
                  className="mt-3 text-sm text-rose-400 hover:text-rose-300 font-medium transition-colors"
                >
                  ← Try Again
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Loading State */}
        {mutation.isPending && (
          <div className="mt-12 text-center animate-fadeIn">
            <div className="inline-flex flex-col items-center gap-4 px-8 py-6 rounded-2xl
                            bg-gradient-to-br from-slate-800/80 to-slate-900/80 
                            border border-purple-500/30 backdrop-blur-sm
                            shadow-xl shadow-purple-500/10">
              <div className="relative w-16 h-16">
                <div className="absolute inset-0 rounded-full border-4 border-purple-500/20" />
                <div className="absolute inset-0 rounded-full border-4 border-transparent border-t-purple-500 animate-spin" />
                <div className="absolute inset-2 rounded-full border-4 border-transparent border-t-blue-400 animate-spin" style={{ animationDirection: "reverse", animationDuration: "1.5s" }} />
                <span className="absolute inset-0 flex items-center justify-center text-2xl">✈️</span>
              </div>
              <div>
                <p className="text-white font-semibold text-lg">Crafting your adventure...</p>
                <p className="text-sm text-slate-400 mt-1">Our AI is planning the perfect trip for you</p>
              </div>
            </div>
          </div>
        )}

        {/* Results Section */}
        {itinerary && (
          <section className="mt-8 animate-fadeIn">
            <ItineraryResult itinerary={itinerary} onReset={() => setItinerary(null)} />
          </section>
        )}

        {/* Footer */}
        <footer className="mt-24 pt-8 border-t border-slate-800/50 text-center">
          <div className="flex items-center justify-center gap-2 text-sm text-slate-500">
            <span>Powered by</span>
            <span className="font-semibold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
              Gemini AI
            </span>
            <span>•</span>
            <span>Built with 💜 for travelers</span>
          </div>
        </footer>
      </main>
    </div>
  );
}
