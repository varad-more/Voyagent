# Agentic LLM Trip Planner (Gemini + FastAPI + Next.js)

Production-ready monorepo for an **agentic trip planner** that builds validated,
weather-aware, day-by-day itineraries. The backend orchestrates specialized agents
using **Google Gemini** and external travel tools with cache fallback.

## Monorepo layout

```
/backend   FastAPI + SQLAlchemy + Alembic + Gemini orchestrator
/frontend  Next.js App Router + Tailwind + TanStack Query
```

## Workflow overview

1. Frontend collects trip preferences and sends a request to the backend.
2. The orchestrator runs specialist agents:
   - PlannerAgent: day-by-day skeleton
   - WeatherAgent: forecast + risks + adjustments
   - AttractionsAgent: top nearby places
   - SchedulerAgent: timed itinerary + buffers
   - FoodAgent: meals by preference + proximity
   - BudgetAgent: budget breakdown + downgrade plan
   - ValidatorAgent: overlap and feasibility checks
3. Results + agent traces are stored in Postgres/SQLite.
4. Frontend renders the itinerary and exports a .ics calendar.

## Backend (FastAPI)

### Requirements
- Python 3.11+
- Postgres for production (SQLite supported for dev)
- Optional Redis for cache

### Setup
```
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
```

### Migrations
```
alembic upgrade head
```

### Run
```
uvicorn app.main:app --reload
```

### Environment variables
```
TRIP_DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/trips
TRIP_REDIS_URL=redis://localhost:6379/0
TRIP_GEMINI_API_KEY=your_key
TRIP_GEMINI_MODEL=gemini-1.5-flash
TRIP_OPENWEATHER_API_KEY=your_key
TRIP_GOOGLE_PLACES_API_KEY=your_key
TRIP_DISTANCE_MATRIX_API_KEY=your_key
TRIP_CURRENCY_API_KEY=your_key
```

### API Endpoints
- `POST /api/itineraries/generate` - synchronous generation
- `POST /api/itineraries` - async queue (BackgroundTasks)
- `GET /api/itineraries/{id}` - retrieve itinerary
- `GET /api/itineraries/{id}/ics` - download calendar

### Sample request
```
POST /api/itineraries/generate
{
  "destination": "Lisbon, Portugal",
  "start_date": "2026-03-10",
  "end_date": "2026-03-12",
  "travelers": { "adults": 2, "children": 0 },
  "origin_location": "San Francisco, CA",
  "food_preferences": {
    "cuisines": ["seafood", "portuguese"],
    "dietary_restrictions": ["vegetarian"],
    "avoid_ingredients": ["peanuts"]
  },
  "activity_preferences": {
    "interests": ["history", "food", "nightlife"],
    "pace": "moderate",
    "accessibility_needs": []
  },
  "lodging_preferences": {
    "lodging_type": "hotel",
    "max_distance_km_from_center": 4
  },
  "budget": { "currency": "USD", "total_budget": 1800, "comfort_level": "midrange" },
  "daily_start_time": "09:00:00",
  "daily_end_time": "20:00:00",
  "notes": "Anniversary trip, prefer walkable areas."
}
```

## Frontend (Next.js)

### Setup
```
cd frontend
npm install
```

### Run
```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 npm run dev
```

## Getting API keys

The app works without API keys (uses safe stubs), but results improve with keys.

### Gemini (required for full LLM planning)
1. Go to Google AI Studio: https://aistudio.google.com/app/apikey
2. Create an API key.
3. Set `TRIP_GEMINI_API_KEY` in `backend/.env`.

### OpenWeather (forecast)
1. Create an account: https://home.openweathermap.org/users/sign_up
2. Generate an API key: https://home.openweathermap.org/api_keys
3. Set `TRIP_OPENWEATHER_API_KEY`.

### Google Places API (attractions)
1. Create a Google Cloud project: https://console.cloud.google.com/
2. Enable Places API: https://console.cloud.google.com/apis/library/places-backend.googleapis.com
3. Create an API key: https://console.cloud.google.com/apis/credentials
4. Set `TRIP_GOOGLE_PLACES_API_KEY`.

### Google Distance Matrix (travel time)
1. Enable Distance Matrix API: https://console.cloud.google.com/apis/library/distance-matrix-backend.googleapis.com
2. Create an API key: https://console.cloud.google.com/apis/credentials
3. Set `TRIP_DISTANCE_MATRIX_API_KEY`.
4. If missing, the backend will use OSRM (public) for coordinate-based routes.

### Currency conversion (optional)
1. Sign up for a currency provider (example: https://exchangerate.host/).
2. Set `TRIP_CURRENCY_API_KEY` if required by your provider.
3. If missing, the backend uses a 1:1 fallback.

## Notes
- All external API calls are cached in DB with TTL and optionally Redis.
- Gemini responses are strictly validated by Pydantic v2 with JSON repair retries.
- Agent traces (drafts/issues/final) are persisted per itinerary.