# ✈️ Voyagent — Your AI Travel Crew

> **Stop Planning. Start Traveling.**

Voyagent is an AI-powered trip planning application built with Django and Google Gemini. Its agentic architecture uses 8 specialized AI agents — each handling a different aspect of travel planning — coordinated by an orchestrator to craft comprehensive, personalized itineraries.

---

## 🗺️ Build & Roadmap Docs

- Implementation plan: `docs/IMPLEMENTATION_PLAN.md`
- Feature backlog: `docs/FEATURE_SUGGESTIONS.md`

These docs explain how to replicate Voyagent-style architecture on another machine/team and what to build next.

---

## 📖 About the Project

### Inspiration

Travel planning is notoriously fragmented. We juggle hotel bookings, flight schedules, weather forecasts, and "Top 10" lists across a dozen browser tabs. The mental load of piecing it all together into a coherent itinerary is immense.

I built **Voyagent** to solve this chaos. Inspired by the promise of agentic AI, I wanted to create a system where specialized agents work together—just like a human travel agency team—to handle the complexity for you.

### How it was Built

Voyagent leverages a **multi-agent architecture** powered by Google Gemini. Each aspect of the trip is handled by a dedicated AI agent:

- **Research Agent**: Scours data for accommodation and transport.
- **Attractions Agent**: Finds hidden gems and top-rated spots.
- **Scheduler Agent**: The logic core that fits activities into time blocks.
- **Orchestrator**: The conductor that ensures agents pass data correctly.

The backend is **Django** for robust data management, while the frontend uses vanilla **JavaScript/CSS** for a fast, responsive experience.

### Challenges & Solutions

**1. Managing AI Hallucinations**
Large Language Models can be unpredictable. To ensure reliability, we implemented a **Validator Agent** that double-checks the final itinerary for logical consistency.

**2. Handling API Limits**
We faced frequent `429 Resource Exhausted` errors from the Gemini API.
*   **Solution**: We implemented an exponential backoff retry strategy and a robust "stub" system that provides fallback data, ensuring the app never crashes even when the AI is down.

### Mathematical Logic

A core challenge was scoring attractions ($S$) based on user interest ($I$), rating ($R$), and uniqueness ($U$):

$$ S = w_1 \cdot I + w_2 \cdot \frac{R}{5} + w_3 \cdot U $$

To ensure valid scheduling, we check:

$$ T_{end}(A) + T_{travel}(A \to B) + T_{buffer} \le T_{start}(B) $$

---

## ✨ Features

- **🤖 8 AI Agents** — Planner, Research, Weather, Attractions, Scheduler, Food, Budget, Validator
- **🌤️ Weather-Aware** — Real-time forecasts adjust your outdoor plans automatically
- **📍 Smart Routing** — Multi-city road trips with optimized scheduling
- **💰 Budget Planning** — Detailed cost breakdowns with currency conversion
- **🍽️ Meal Planning** — Restaurant suggestions aligned with dietary preferences
- **📅 Calendar Export** — Download your itinerary as an ICS file
- **🔍 Location Autocomplete** — Google Places–powered suggestions as you type
- **🛡️ Graceful Fallbacks** — Stub data when API keys are missing, so the app always works

---

## 🏗️ Architecture

```mermaid
graph TD
    A[User Request] --> B[Orchestrator]
    B --> C[ResearchAgent]
    B --> D[PlannerAgent]
    D --> E[WeatherAgent]
    D --> F[AttractionsAgent]
    E --> G[SchedulerAgent]
    F --> G
    G --> H[FoodAgent]
    H --> I[BudgetAgent]
    I --> J[ValidatorAgent]
    J --> K[Final Itinerary]
```

## Project Structure

```
trip-scheduler-agentic-llm/
├── manage.py                    # Django management script
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Production container
├── entrypoint.sh                # Production startup (migrate + gunicorn)
├── docker-compose.yml           # Local Docker setup
├── .env.example                 # Environment variables template
│
├── tests/                       # Test suite (192 tests)
│   ├── conftest.py              # Shared fixtures
│   ├── test_models.py           # Model tests
│   ├── test_serializers.py      # Serializer validation
│   ├── test_utils.py            # Utility function tests
│   ├── test_cache.py            # Cache layer tests
│   ├── test_orchestrator.py     # Pipeline integration tests
│   ├── test_api.py              # API endpoint tests
│   ├── test_unknown_locations.py # Obscure/non-English location tests
│   ├── test_services/           # Service-level tests
│   └── test_agents/             # Agent-level tests
│
└── trip_planner/                # Main Django application
    ├── settings.py              # Django settings
    ├── urls.py                  # Root URL configuration
    ├── wsgi.py / asgi.py        # Server interfaces
    │
    ├── models/                  # Database models
    │   ├── itinerary.py         # Itinerary model
    │   ├── trace.py             # Agent trace model
    │   └── cache.py             # External cache model
    │
    ├── api/                     # REST API
    │   ├── serializers.py       # Request/response serializers
    │   ├── urls.py              # API routes
    │   └── views/               # API views
    │       ├── itineraries.py   # Itinerary CRUD + generate
    │       ├── places.py        # Location autocomplete proxy
    │       ├── analysis.py      # Image analysis
    │       └── edit.py          # Block editing
    │
    ├── agents/                  # AI Agents (8 total)
    │   ├── base.py              # Base agent class
    │   ├── planner.py           # Day-by-day planning
    │   ├── research.py          # Accommodation/transport research
    │   ├── weather.py           # Weather analysis & adjustments
    │   ├── attractions.py       # Attraction ranking
    │   ├── scheduler.py         # Timed schedule creation
    │   ├── food.py              # Meal planning
    │   ├── budget.py            # Cost calculation
    │   └── validator.py         # Schedule validation
    │
    ├── services/                # External integrations
    │   ├── orchestrator.py      # Agent coordination pipeline
    │   ├── gemini.py            # Gemini AI client
    │   ├── places.py            # Google Places API
    │   ├── weather.py           # OpenWeather API
    │   ├── travel_time.py       # Distance/travel time
    │   └── currency.py          # Currency conversion
    │
    ├── core/                    # Utilities
    │   ├── cache.py             # Cache client
    │   ├── exceptions.py        # Custom exceptions
    │   └── utils.py             # Helper functions
    │
    ├── static/                  # Frontend assets
    │   ├── css/styles.css       # Full design system
    │   └── js/app.js            # Frontend JavaScript
    │
    └── templates/               # Django templates
        ├── base.html            # Base layout
        └── index.html           # Main trip planner page
```

---

## 🚀 Quick Start

### 1. Create Conda Environment

```bash
conda create -n trip-planner python=3.11 -y
conda activate trip-planner
```

### 2. Install Dependencies

```bash
cd trip-scheduler-agentic-llm
pip install -r requirements.txt
```

### 3. Configure Environment Variables

```bash
cp .env.example .env
# Edit .env with your API keys (see API Keys section below)
```

### 4. Initialize Database

```bash
python manage.py migrate
python manage.py createcachetable   # Only needed if not using Redis
```

### 5. Run Development Server

```bash
python manage.py runserver
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

---

## 🔑 API Keys

### Required

| Key | Purpose | Get It |
|-----|---------|--------|
| `GEMINI_API_KEY` | AI reasoning & content generation | [Google AI Studio](https://makersuite.google.com/app/apikey) |

### Optional (app works without these using stub data)

| Key | Purpose | Get It |
|-----|---------|--------|
| `OPENWEATHER_API_KEY` | Real-time weather forecasts | [OpenWeather](https://openweathermap.org/api) |
| `GOOGLE_PLACES_API_KEY` | Attraction details & autocomplete | [Google Cloud Console](https://console.cloud.google.com/) |
| `DISTANCE_MATRIX_API_KEY` | Precise travel times | Same GCP project or separate key |
| `CURRENCY_API_KEY` | Currency conversion rates | [ExchangeRate API](https://www.exchangerate-api.com/) |

### Gemini Model Selection

| Model ID | Best For |
|----------|----------|
| `gemini-2.0-flash` | ⭐ Recommended — best balance of speed + quality |
| `gemini-2.0-flash-lite` | Lower latency, reduced cost |
| `gemini-2.5-flash` | Advanced reasoning with speed |
| `gemini-2.5-pro` | Complex tasks requiring highest accuracy |

> [!NOTE]
> Older models (`gemini-1.5-flash`, `gemini-pro`) are deprecated. Use `gemini-2.0-flash` or newer.

### Validate Your Keys

```bash
python manage.py test_keys      # Test all configured API keys
python manage.py list_models    # List available Gemini models
```

### Google Maps Platform Setup

1. Create a project at [Google Cloud Console](https://console.cloud.google.com/)
2. Enable **Places API (New)** and **Distance Matrix API**
3. Create an API key under **Credentials**
4. Add key restrictions for security (restrict to Places + Distance Matrix only)
5. Add to `.env`:
   ```
   GOOGLE_PLACES_API_KEY=your_key
   DISTANCE_MATRIX_API_KEY=your_key
   ```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/api/itineraries/` | Queue async generation |
| `POST` | `/api/itineraries/generate` | Generate itinerary (sync) |
| `GET` | `/api/itineraries/<id>/` | Get itinerary details |
| `PATCH` | `/api/itineraries/<id>/` | Update itinerary |
| `GET` | `/api/itineraries/<id>/ics` | Download ICS calendar |
| `GET` | `/api/places/autocomplete?q=<query>` | Location autocomplete |
| `POST` | `/api/analysis/image` | Analyze travel image |
| `POST` | `/api/edit/block` | Edit schedule block |

### Example Request

```bash
curl -X POST http://localhost:8000/api/itineraries/generate \
  -H "Content-Type: application/json" \
  -d '{
    "destination": "Tokyo, Japan",
    "start_date": "2026-04-01",
    "end_date": "2026-04-05",
    "travelers": {"adults": 2, "children": 0},
    "budget": {
      "currency": "USD",
      "total_budget": 3000,
      "comfort_level": "midrange"
    },
    "activity_preferences": {
      "interests": ["culture", "food", "history"],
      "pace": "moderate"
    }
  }'
```

---

## 🧪 Testing

The project includes a comprehensive test suite with **192 tests** covering all layers.

```bash
# Run all tests
python -m pytest tests/ -v

# Quick summary
python -m pytest tests/ --tb=short -q

# Run specific test categories
python -m pytest tests/test_agents/ -v        # Agent tests
python -m pytest tests/test_services/ -v      # Service tests
python -m pytest tests/test_api.py -v         # API endpoint tests
python -m pytest tests/test_orchestrator.py   # Pipeline integration
```

### Test Coverage

| Category | Tests | What's Covered |
|----------|-------|----------------|
| Models | 10 | Itinerary lifecycle, AgentTrace, ExternalCache |
| Serializers | 16 | Validation rules, defaults, edge cases |
| Utilities | 13 | JSON parsing, ICS generation |
| Cache | 11 | Key generation, get/set, expiry |
| Services | 25 | Weather, places, travel time, currency |
| Agents | 39 | All 8 agents with stub + mock Gemini |
| API | 18 | CRUD, generate, ICS, autocomplete, health |
| Orchestrator | 7 | Full pipeline, packing list, error handling |
| Unknown Locations | 53 | Obscure, non-English, multi-city destinations |

---

## 🏭 Production Deployment

### Environment Variables

```bash
DJANGO_SECRET_KEY=<generate-a-strong-key>    # python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=postgres://user:pass@host:5432/voyagent
GEMINI_API_KEY=your-production-key
```

### Docker

```bash
# Build and run
docker build -t voyagent .
docker run -p 8080:8080 --env-file .env voyagent

# Or with docker-compose
docker-compose up --build
```

### Google Cloud Run

```bash
# Build and push
gcloud builds submit --tag gcr.io/PROJECT_ID/voyagent

# Deploy
gcloud run deploy voyagent \
  --image gcr.io/PROJECT_ID/voyagent \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars="DJANGO_DEBUG=False,DJANGO_SECRET_KEY=<key>,GEMINI_API_KEY=<key>"
```

Set `CLOUD_RUN_SERVICE_URL` to your deployed URL for CSRF/allowed hosts to work automatically.

### Production Checklist

- [ ] `DJANGO_DEBUG=False`
- [ ] Strong, unique `DJANGO_SECRET_KEY` (generate with command above)
- [ ] `DJANGO_ALLOWED_HOSTS` set to your domain(s)
- [ ] PostgreSQL via `DATABASE_URL` (not SQLite)
- [ ] `GEMINI_API_KEY` configured
- [ ] Static files served via WhiteNoise (built-in)
- [ ] HTTPS via reverse proxy or cloud provider
- [ ] `CORS_ALLOW_ALL_ORIGINS` is automatically `False` when `DEBUG=False`

---

## 🤖 Agent Architecture

| # | Agent | Role |
|---|-------|------|
| 1 | **ResearchAgent** | Researches accommodation & transport options |
| 2 | **PlannerAgent** | Creates day-by-day skeleton plans |
| 3 | **WeatherAgent** | Fetches weather & suggests schedule adjustments |
| 4 | **AttractionsAgent** | Finds & ranks top attractions |
| 5 | **SchedulerAgent** | Converts plans to timed, non-overlapping blocks |
| 6 | **FoodAgent** | Plans meals aligned with schedule & dietary needs |
| 7 | **BudgetAgent** | Calculates costs with currency conversion |
| 8 | **ValidatorAgent** | Validates schedule for overlaps & time conflicts |

Each agent produces a structured JSON output that feeds into the next, with the orchestrator managing the pipeline. If Gemini is unavailable, agents gracefully fall back to rule-based stub outputs.

---

## 📋 Development

```bash
# Run tests
python -m pytest tests/ -v

# Create superuser for admin
python manage.py createsuperuser

# Access admin at http://localhost:8000/admin/
```

---

<p align="center">
  <strong>Voyagent</strong> — Powered by Gemini AI ✨
</p>
