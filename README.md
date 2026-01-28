# Agentic LLM Trip Planner (Gemini + FastAPI + Next.js)

Production-ready monorepo for an **agentic trip planner** that builds validated,
weather-aware, day-by-day itineraries. The backend orchestrates specialized agents
using **Google Gemini** and external travel tools with cache fallback.

## Monorepo layout

```
/backend   FastAPI + SQLAlchemy + Alembic + Gemini orchestrator
/frontend  Next.js App Router + Tailwind + TanStack Query
```

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

## Notes
- All external API calls are cached in DB with TTL and optionally Redis.
- Gemini responses are strictly validated by Pydantic v2 with JSON repair retries.
- Agent traces (drafts/issues/final) are persisted per itinerary.