"use client";

import { useState, useRef, useEffect } from "react";
import { tripRequestSchema, TripRequest } from "@/lib/validation";

type TripFormProps = {
  onSubmit: (payload: TripRequest) => void;
  isLoading: boolean;
};

// Popular destination suggestions
const DESTINATION_SUGGESTIONS = [
  // California - Cities & Towns
  "San Francisco, California",
  "Los Angeles, California",
  "San Diego, California",
  "Santa Barbara, California",
  "Monterey, California",
  "Carmel-by-the-Sea, California",
  "Palm Springs, California",
  "Napa Valley, California",
  "Lake Tahoe, California",
  "Big Sur, California",
  "Laguna Beach, California",
  "Sausalito, California",
  "Solvang, California",
  // California - National Parks
  "Yosemite National Park, California",
  "Joshua Tree National Park, California",
  "Death Valley National Park, California",
  "Sequoia National Park, California",
  "Kings Canyon National Park, California",
  "Redwood National Park, California",
  "Channel Islands National Park, California",
  "Pinnacles National Park, California",
  "Lassen Volcanic National Park, California",

  // Arizona - Cities & Towns
  "Phoenix, Arizona",
  "Scottsdale, Arizona",
  "Sedona, Arizona",
  "Tucson, Arizona",
  "Flagstaff, Arizona",
  "Jerome, Arizona",
  "Bisbee, Arizona",
  "Tombstone, Arizona",
  "Page, Arizona",
  "Williams, Arizona",
  // Arizona - National Parks & Monuments
  "Grand Canyon National Park, Arizona",
  "Petrified Forest National Park, Arizona",
  "Saguaro National Park, Arizona",
  "Monument Valley, Arizona",
  "Antelope Canyon, Arizona",
  "Horseshoe Bend, Arizona",
  "Havasu Falls, Arizona",

  // Utah - Cities & Towns
  "Salt Lake City, Utah",
  "Park City, Utah",
  "Moab, Utah",
  "St. George, Utah",
  "Springdale, Utah",
  "Kanab, Utah",
  "Torrey, Utah",
  // Utah - National Parks (Mighty 5)
  "Zion National Park, Utah",
  "Bryce Canyon National Park, Utah",
  "Arches National Park, Utah",
  "Canyonlands National Park, Utah",
  "Capitol Reef National Park, Utah",
  "Goblin Valley State Park, Utah",
  "Dead Horse Point, Utah",
  "The Wave, Utah",

  // International Destinations
  "Tokyo, Japan",
  "Paris, France",
  "New York, USA",
  "Rome, Italy",
  "Barcelona, Spain",
  "London, UK",
  "Sydney, Australia",
  "Dubai, UAE",
  "Singapore",
  "Bali, Indonesia",
  "Amsterdam, Netherlands",
  "Bangkok, Thailand",
  "Prague, Czech Republic",
  "Santorini, Greece",
  "Reykjavik, Iceland",
  "Machu Picchu, Peru",
  "Cape Town, South Africa",
  "Kyoto, Japan",
  "Marrakech, Morocco",
  "Vienna, Austria",
];

// Common cuisine suggestions
const CUISINE_SUGGESTIONS = [
  "Italian",
  "Japanese",
  "Mexican",
  "Thai",
  "Indian",
  "French",
  "Chinese",
  "Mediterranean",
  "Korean",
  "Vietnamese",
  "Spanish",
  "Greek",
  "Middle Eastern",
  "American",
  "Seafood",
];

// Interest suggestions
const INTEREST_SUGGESTIONS = [
  "Museums",
  "Food & Dining",
  "Architecture",
  "Nature",
  "Nightlife",
  "Shopping",
  "History",
  "Art",
  "Adventure",
  "Photography",
  "Local Culture",
  "Beaches",
  "Hiking",
  "Wine & Spirits",
  "Street Food",
];

// Currency options
const CURRENCIES = [
  { code: "USD", symbol: "$", name: "US Dollar" },
  { code: "EUR", symbol: "€", name: "Euro" },
  { code: "GBP", symbol: "£", name: "British Pound" },
  { code: "JPY", symbol: "¥", name: "Japanese Yen" },
  { code: "AUD", symbol: "A$", name: "Australian Dollar" },
  { code: "CAD", symbol: "C$", name: "Canadian Dollar" },
  { code: "INR", symbol: "₹", name: "Indian Rupee" },
  { code: "SGD", symbol: "S$", name: "Singapore Dollar" },
];

const defaultValues = {
  destination: "",
  start_date: "",
  end_date: "",
  adults: 2,
  children: 0,
  origin_location: "",
  cuisines: [] as string[],
  dietary_restrictions: "",
  avoid_ingredients: "",
  interests: [] as string[],
  pace: "moderate",
  lodging_type: "any",
  max_distance_km_from_center: 5,
  currency: "USD",
  total_budget: 1500,
  comfort_level: "midrange",
  daily_start_time: "09:00",
  daily_end_time: "20:00",
  notes: "",
};

// Autocomplete Input Component
function AutocompleteInput({
  label,
  value,
  onChange,
  suggestions,
  placeholder,
  icon,
  required = false,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  suggestions: string[];
  placeholder: string;
  icon: React.ReactNode;
  required?: boolean;
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [filteredSuggestions, setFilteredSuggestions] = useState<string[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (value) {
      const filtered = suggestions.filter((s) =>
        s.toLowerCase().includes(value.toLowerCase())
      );
      setFilteredSuggestions(filtered.slice(0, 6));
    } else {
      setFilteredSuggestions(suggestions.slice(0, 6));
    }
  }, [value, suggestions]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node) &&
        !inputRef.current?.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div className="relative group">
      <label className="block text-sm font-medium text-slate-300 mb-2">
        {label}
        {required && <span className="text-emerald-400 ml-1">*</span>}
      </label>
      <div className="relative">
        <span className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-emerald-400 transition-colors">
          {icon}
        </span>
        <input
          ref={inputRef}
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onFocus={() => setIsOpen(true)}
          placeholder={placeholder}
          required={required}
          className="w-full pl-12 pr-4 py-3.5 bg-slate-900/50 border border-slate-700/50 rounded-xl
                     text-white placeholder-slate-500
                     focus:outline-none focus:ring-2 focus:ring-emerald-500/40 focus:border-emerald-500/50
                     hover:border-slate-600 transition-all duration-200
                     backdrop-blur-sm"
        />
      </div>
      {isOpen && filteredSuggestions.length > 0 && (
        <div
          ref={dropdownRef}
          className="absolute z-[100] w-full mt-2 bg-slate-800/95 border border-slate-700/50 rounded-xl
                     shadow-xl shadow-black/20 backdrop-blur-md overflow-hidden animate-fadeIn"
        >
          {filteredSuggestions.map((suggestion, index) => (
            <button
              key={suggestion}
              type="button"
              onClick={() => {
                onChange(suggestion);
                setIsOpen(false);
              }}
              className={`w-full px-4 py-3 text-left text-sm hover:bg-emerald-500/10 
                         transition-colors flex items-center gap-3
                         ${index !== filteredSuggestions.length - 1 ? "border-b border-slate-700/30" : ""}`}
            >
              <span className="text-emerald-400">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </span>
              <span className="text-slate-200">{suggestion}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

// Tag Input Component for multi-select
function TagInput({
  label,
  selectedTags,
  onTagsChange,
  suggestions,
  placeholder,
  icon,
}: {
  label: string;
  selectedTags: string[];
  onTagsChange: (tags: string[]) => void;
  suggestions: string[];
  placeholder: string;
  icon: React.ReactNode;
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [inputValue, setInputValue] = useState("");
  const dropdownRef = useRef<HTMLDivElement>(null);

  const availableSuggestions = suggestions.filter(
    (s) => !selectedTags.includes(s) && s.toLowerCase().includes(inputValue.toLowerCase())
  );

  const addTag = (tag: string) => {
    if (!selectedTags.includes(tag)) {
      onTagsChange([...selectedTags, tag]);
    }
    setInputValue("");
  };

  const removeTag = (tag: string) => {
    onTagsChange(selectedTags.filter((t) => t !== tag));
  };

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div className="relative" ref={dropdownRef}>
      <label className="block text-sm font-medium text-slate-300 mb-2">{label}</label>
      <div
        className="min-h-[54px] p-2 bg-slate-900/50 border border-slate-700/50 rounded-xl
                   focus-within:ring-2 focus-within:ring-emerald-500/40 focus-within:border-emerald-500/50
                   hover:border-slate-600 transition-all duration-200 backdrop-blur-sm"
      >
        <div className="flex flex-wrap gap-2">
          {selectedTags.map((tag) => (
            <span
              key={tag}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-emerald-500/20 
                         text-emerald-300 text-sm rounded-lg border border-emerald-500/30
                         animate-scaleIn"
            >
              {tag}
              <button
                type="button"
                onClick={() => removeTag(tag)}
                className="hover:text-emerald-100 transition-colors"
              >
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </span>
          ))}
          <div className="flex items-center gap-2 flex-1 min-w-[120px]">
            <span className="text-slate-400">{icon}</span>
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onFocus={() => setIsOpen(true)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && inputValue.trim()) {
                  e.preventDefault();
                  addTag(inputValue.trim());
                }
              }}
              placeholder={selectedTags.length === 0 ? placeholder : "Add more..."}
              className="flex-1 bg-transparent border-none outline-none text-white 
                         placeholder-slate-500 text-sm py-1.5"
            />
          </div>
        </div>
      </div>
      {isOpen && availableSuggestions.length > 0 && (
        <div
          className="absolute z-[100] w-full mt-2 bg-slate-800/95 border border-slate-700/50 rounded-xl
                     shadow-xl shadow-black/20 backdrop-blur-md overflow-hidden max-h-48 overflow-y-auto animate-fadeIn"
        >
          {availableSuggestions.slice(0, 8).map((suggestion, index) => (
            <button
              key={suggestion}
              type="button"
              onClick={() => addTag(suggestion)}
              className={`w-full px-4 py-2.5 text-left text-sm hover:bg-emerald-500/10 
                         transition-colors text-slate-200
                         ${index !== Math.min(availableSuggestions.length, 8) - 1 ? "border-b border-slate-700/30" : ""}`}
            >
              {suggestion}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

// Number Stepper Component
function NumberStepper({
  label,
  value,
  onChange,
  min = 0,
  max = 99,
  icon,
}: {
  label: string;
  value: number;
  onChange: (value: number) => void;
  min?: number;
  max?: number;
  icon: React.ReactNode;
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-slate-300 mb-2">{label}</label>
      <div className="flex items-center gap-3 bg-slate-900/50 border border-slate-700/50 rounded-xl p-2 
                      hover:border-slate-600 transition-all duration-200">
        <span className="text-slate-400 pl-2">{icon}</span>
        <button
          type="button"
          onClick={() => onChange(Math.max(min, value - 1))}
          disabled={value <= min}
          className="w-10 h-10 rounded-lg bg-slate-800 hover:bg-slate-700 
                     disabled:opacity-40 disabled:cursor-not-allowed
                     flex items-center justify-center transition-colors"
        >
          <svg className="w-5 h-5 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
          </svg>
        </button>
        <span className="w-12 text-center text-xl font-semibold text-white">{value}</span>
        <button
          type="button"
          onClick={() => onChange(Math.min(max, value + 1))}
          disabled={value >= max}
          className="w-10 h-10 rounded-lg bg-slate-800 hover:bg-slate-700 
                     disabled:opacity-40 disabled:cursor-not-allowed
                     flex items-center justify-center transition-colors"
        >
          <svg className="w-5 h-5 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
        </button>
      </div>
    </div>
  );
}

// Custom Select Component
function CustomSelect({
  label,
  value,
  onChange,
  options,
  icon,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: { value: string; label: string; description?: string }[];
  icon: React.ReactNode;
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-slate-300 mb-2">{label}</label>
      <div className="relative">
        <span className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none">
          {icon}
        </span>
        <select
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="w-full appearance-none pl-12 pr-10 py-3.5 bg-slate-900/50 border border-slate-700/50 rounded-xl
                     text-white cursor-pointer
                     focus:outline-none focus:ring-2 focus:ring-emerald-500/40 focus:border-emerald-500/50
                     hover:border-slate-600 transition-all duration-200"
        >
          {options.map((opt) => (
            <option key={opt.value} value={opt.value} className="bg-slate-800">
              {opt.label}
            </option>
          ))}
        </select>
        <span className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </span>
      </div>
    </div>
  );
}

// Section Header Component
function SectionHeader({ title, icon, description }: { title: string; icon: React.ReactNode; description?: string }) {
  return (
    <div className="flex items-center gap-3 pb-4 border-b border-purple-500/20">
      <div className="p-2.5 bg-gradient-to-br from-blue-500/20 to-purple-500/20 rounded-xl text-purple-400 icon-glow">
        {icon}
      </div>
      <div>
        <h3 className="text-lg font-semibold text-white">{title}</h3>
        {description && <p className="text-sm text-slate-400">{description}</p>}
      </div>
    </div>
  );
}

export function TripForm({ onSubmit, isLoading }: TripFormProps) {
  const [values, setValues] = useState(defaultValues);
  const [error, setError] = useState<string | null>(null);

  const updateField = <K extends keyof typeof defaultValues>(
    field: K,
    value: typeof defaultValues[K]
  ) => {
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
        cuisines: values.cuisines,
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
        interests: values.interests,
        pace: values.pace as TripRequest["activity_preferences"]["pace"],
        accessibility_needs: [],
      },
      lodging_preferences: {
        lodging_type: values.lodging_type as TripRequest["lodging_preferences"]["lodging_type"],
        max_distance_km_from_center: Number(values.max_distance_km_from_center),
      },
      budget: {
        currency: values.currency,
        total_budget: Number(values.total_budget),
        comfort_level: values.comfort_level as TripRequest["budget"]["comfort_level"],
      },
      daily_start_time: values.daily_start_time + ":00",
      daily_end_time: values.daily_end_time + ":00",
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
    <form onSubmit={handleSubmit} className="space-y-8">
      {/* Error Display */}
      {error && (
        <div className="flex items-center gap-3 p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl animate-shake">
          <svg className="w-5 h-5 text-rose-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span className="text-rose-200 text-sm">{error}</span>
        </div>
      )}

      {/* Hero Section - Destination & Dates */}
      <div className="relative rounded-2xl glass-card p-6">
        <div className="absolute top-0 right-0 w-64 h-64 bg-emerald-500/5 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2" />

        <SectionHeader
          title="Where & When"
          icon={
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
          description="Start by choosing your dream destination"
        />

        <div className="mt-6 grid gap-6 md:grid-cols-2">
          <AutocompleteInput
            label="Destination"
            value={values.destination}
            onChange={(v) => updateField("destination", v)}
            suggestions={DESTINATION_SUGGESTIONS}
            placeholder="Where do you want to go?"
            required
            icon={
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
              </svg>
            }
          />
          <AutocompleteInput
            label="Origin"
            value={values.origin_location}
            onChange={(v) => updateField("origin_location", v)}
            suggestions={DESTINATION_SUGGESTIONS}
            placeholder="Where are you traveling from?"
            icon={
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
              </svg>
            }
          />
        </div>

        <div className="mt-6 grid gap-6 md:grid-cols-2">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Start Date <span className="text-emerald-400">*</span>
            </label>
            <div className="relative">
              <span className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </span>
              <input
                type="date"
                value={values.start_date}
                onChange={(e) => updateField("start_date", e.target.value)}
                required
                className="w-full pl-12 pr-4 py-3.5 bg-slate-900/50 border border-slate-700/50 rounded-xl
                           text-white [color-scheme:dark]
                           focus:outline-none focus:ring-2 focus:ring-emerald-500/40 focus:border-emerald-500/50
                           hover:border-slate-600 transition-all duration-200"
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              End Date <span className="text-emerald-400">*</span>
            </label>
            <div className="relative">
              <span className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </span>
              <input
                type="date"
                value={values.end_date}
                onChange={(e) => updateField("end_date", e.target.value)}
                min={values.start_date}
                required
                className="w-full pl-12 pr-4 py-3.5 bg-slate-900/50 border border-slate-700/50 rounded-xl
                           text-white [color-scheme:dark]
                           focus:outline-none focus:ring-2 focus:ring-emerald-500/40 focus:border-emerald-500/50
                           hover:border-slate-600 transition-all duration-200"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Travelers Section */}
      <div className="rounded-2xl glass-card p-6">
        <SectionHeader
          title="Travelers"
          icon={
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
          }
          description="Who's coming along?"
        />
        <div className="mt-6 grid gap-6 md:grid-cols-2">
          <NumberStepper
            label="Adults"
            value={values.adults}
            onChange={(v) => updateField("adults", v)}
            min={1}
            max={20}
            icon={
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
            }
          />
          <NumberStepper
            label="Children"
            value={values.children}
            onChange={(v) => updateField("children", v)}
            min={0}
            max={20}
            icon={
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            }
          />
        </div>
      </div>

      {/* Interests & Activities */}
      <div className="rounded-2xl glass-card p-6">
        <SectionHeader
          title="Interests & Activities"
          icon={
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
          description="What do you enjoy doing on vacation?"
        />
        <div className="mt-6 space-y-6">
          <TagInput
            label="Interests"
            selectedTags={values.interests}
            onTagsChange={(tags) => updateField("interests", tags)}
            suggestions={INTEREST_SUGGESTIONS}
            placeholder="Select or type interests..."
            icon={
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
              </svg>
            }
          />
          <CustomSelect
            label="Travel Pace"
            value={values.pace}
            onChange={(v) => updateField("pace", v)}
            options={[
              { value: "slow", label: "🐌 Slow & Relaxed", description: "Fewer activities, more downtime" },
              { value: "moderate", label: "⚖️ Moderate", description: "Balanced mix of activities and rest" },
              { value: "fast", label: "⚡ Fast & Packed", description: "See as much as possible" },
            ]}
            icon={
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            }
          />
        </div>
      </div>

      {/* Food Preferences */}
      <div className="rounded-2xl glass-card p-6">
        <SectionHeader
          title="Food & Dining"
          icon={
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" />
            </svg>
          }
          description="Your culinary preferences"
        />
        <div className="mt-6 space-y-6">
          <TagInput
            label="Favorite Cuisines"
            selectedTags={values.cuisines}
            onTagsChange={(tags) => updateField("cuisines", tags)}
            suggestions={CUISINE_SUGGESTIONS}
            placeholder="Select cuisines you enjoy..."
            icon={
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
            }
          />
          <div className="grid gap-6 md:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Dietary Restrictions
              </label>
              <div className="relative">
                <span className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
                  </svg>
                </span>
                <input
                  type="text"
                  value={values.dietary_restrictions}
                  onChange={(e) => updateField("dietary_restrictions", e.target.value)}
                  placeholder="vegetarian, gluten-free..."
                  className="w-full pl-12 pr-4 py-3.5 bg-slate-900/50 border border-slate-700/50 rounded-xl
                             text-white placeholder-slate-500
                             focus:outline-none focus:ring-2 focus:ring-emerald-500/40 focus:border-emerald-500/50
                             hover:border-slate-600 transition-all duration-200"
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Ingredients to Avoid
              </label>
              <div className="relative">
                <span className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                </span>
                <input
                  type="text"
                  value={values.avoid_ingredients}
                  onChange={(e) => updateField("avoid_ingredients", e.target.value)}
                  placeholder="peanuts, shellfish..."
                  className="w-full pl-12 pr-4 py-3.5 bg-slate-900/50 border border-slate-700/50 rounded-xl
                             text-white placeholder-slate-500
                             focus:outline-none focus:ring-2 focus:ring-emerald-500/40 focus:border-emerald-500/50
                             hover:border-slate-600 transition-all duration-200"
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Budget & Accommodation */}
      <div className="rounded-2xl glass-card p-6">
        <SectionHeader
          title="Budget & Stay"
          icon={
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
          description="Set your budget and accommodation preferences"
        />
        <div className="mt-6 space-y-6">
          <div className="grid gap-6 md:grid-cols-3">
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Total Budget
              </label>
              <div className="relative">
                <span className="absolute left-4 top-1/2 -translate-y-1/2 text-emerald-400 font-semibold">
                  {CURRENCIES.find((c) => c.code === values.currency)?.symbol || "$"}
                </span>
                <input
                  type="number"
                  min={0}
                  value={values.total_budget}
                  onChange={(e) => updateField("total_budget", Number(e.target.value))}
                  className="w-full pl-10 pr-4 py-3.5 bg-slate-900/50 border border-slate-700/50 rounded-xl
                             text-white text-lg font-semibold
                             focus:outline-none focus:ring-2 focus:ring-emerald-500/40 focus:border-emerald-500/50
                             hover:border-slate-600 transition-all duration-200"
                />
              </div>
            </div>
            <CustomSelect
              label="Currency"
              value={values.currency}
              onChange={(v) => updateField("currency", v)}
              options={CURRENCIES.map((c) => ({ value: c.code, label: `${c.symbol} ${c.code}` }))}
              icon={
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                </svg>
              }
            />
          </div>
          <div className="grid gap-6 md:grid-cols-2">
            <CustomSelect
              label="Comfort Level"
              value={values.comfort_level}
              onChange={(v) => updateField("comfort_level", v)}
              options={[
                { value: "budget", label: "💰 Budget-Friendly" },
                { value: "midrange", label: "⭐ Midrange" },
                { value: "luxury", label: "✨ Luxury" },
              ]}
              icon={
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                </svg>
              }
            />
            <CustomSelect
              label="Accommodation Type"
              value={values.lodging_type}
              onChange={(v) => updateField("lodging_type", v)}
              options={[
                { value: "any", label: "🏨 Any Type" },
                { value: "hotel", label: "🏢 Hotel" },
                { value: "hostel", label: "🛏️ Hostel" },
                { value: "apartment", label: "🏠 Apartment" },
                { value: "boutique", label: "💎 Boutique" },
              ]}
              icon={
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
              }
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Max Distance from City Center
            </label>
            <div className="flex items-center gap-4">
              <input
                type="range"
                min={1}
                max={20}
                value={values.max_distance_km_from_center}
                onChange={(e) => updateField("max_distance_km_from_center", Number(e.target.value))}
                className="flex-1 h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer
                           [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-5 
                           [&::-webkit-slider-thumb]:h-5 [&::-webkit-slider-thumb]:rounded-full 
                           [&::-webkit-slider-thumb]:bg-emerald-500 [&::-webkit-slider-thumb]:cursor-pointer
                           [&::-webkit-slider-thumb]:shadow-lg [&::-webkit-slider-thumb]:shadow-emerald-500/30"
              />
              <span className="w-20 text-center py-2 px-3 bg-slate-900/50 rounded-lg text-emerald-400 font-semibold">
                {values.max_distance_km_from_center} km
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Schedule & Notes */}
      <div className="rounded-2xl glass-card p-6">
        <SectionHeader
          title="Daily Schedule"
          icon={
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
          description="When do you like to start and end your days?"
        />
        <div className="mt-6 grid gap-6 md:grid-cols-2">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Start Time</label>
            <div className="relative">
              <span className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
              </span>
              <input
                type="time"
                value={values.daily_start_time}
                onChange={(e) => updateField("daily_start_time", e.target.value)}
                className="w-full pl-12 pr-4 py-3.5 bg-slate-900/50 border border-slate-700/50 rounded-xl
                           text-white [color-scheme:dark]
                           focus:outline-none focus:ring-2 focus:ring-emerald-500/40 focus:border-emerald-500/50
                           hover:border-slate-600 transition-all duration-200"
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">End Time</label>
            <div className="relative">
              <span className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                </svg>
              </span>
              <input
                type="time"
                value={values.daily_end_time}
                onChange={(e) => updateField("daily_end_time", e.target.value)}
                className="w-full pl-12 pr-4 py-3.5 bg-slate-900/50 border border-slate-700/50 rounded-xl
                           text-white [color-scheme:dark]
                           focus:outline-none focus:ring-2 focus:ring-emerald-500/40 focus:border-emerald-500/50
                           hover:border-slate-600 transition-all duration-200"
              />
            </div>
          </div>
        </div>
        <div className="mt-6">
          <label className="block text-sm font-medium text-slate-300 mb-2">
            Additional Notes
          </label>
          <textarea
            value={values.notes}
            onChange={(e) => updateField("notes", e.target.value)}
            placeholder="Any special requests, celebrations, must-sees, or accessibility needs..."
            rows={4}
            className="w-full px-4 py-3.5 bg-slate-900/50 border border-slate-700/50 rounded-xl
                       text-white placeholder-slate-500 resize-none
                       focus:outline-none focus:ring-2 focus:ring-emerald-500/40 focus:border-emerald-500/50
                       hover:border-slate-600 transition-all duration-200"
          />
        </div>
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={isLoading}
        className="group relative w-full py-4 px-6 rounded-2xl font-bold text-lg
                   bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500
                   hover:from-blue-400 hover:via-purple-400 hover:to-pink-400
                   disabled:from-slate-600 disabled:to-slate-700 disabled:cursor-not-allowed
                   text-white shadow-xl shadow-purple-500/30
                   transition-all duration-300 transform hover:scale-[1.02] active:scale-[0.98]
                   hover:shadow-2xl hover:shadow-purple-500/40
                   overflow-hidden"
      >
        <span className="relative z-10 flex items-center justify-center gap-3">
          {isLoading ? (
            <>
              <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              Planning Your Adventure...
            </>
          ) : (
            <>
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3l14 9-14 9V3z" />
              </svg>
              Generate My Itinerary
            </>
          )}
        </span>
        {!isLoading && (
          <span className="absolute inset-0 bg-gradient-to-r from-white/0 via-white/20 to-white/0 
                          translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700" />
        )}
      </button>
    </form>
  );
}
