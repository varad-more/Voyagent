# Trip Planner - AI-Powered Trip Scheduling

An AI-powered trip planning application using Django and Google Gemini. Features an agentic architecture with 8 specialized agents for comprehensive trip planning.

## Project Structure

```
trip-scheduler-agentic-llm/
├── manage.py                    # Django management script
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variables template
├── README.md
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
    │       ├── itineraries.py   # Itinerary CRUD
    │       ├── analysis.py      # Image analysis
    │       └── edit.py          # Block editing
    │
    ├── agents/                  # AI Agents
    │   ├── base.py              # Base agent class
    │   ├── planner.py           # Day-by-day planning
    │   ├── research.py          # Accommodation/transport research
    │   ├── weather.py           # Weather analysis
    │   ├── attractions.py       # Attraction ranking
    │   ├── scheduler.py         # Timed schedule creation
    │   ├── food.py              # Meal planning
    │   ├── budget.py            # Cost calculation
    │   └── validator.py         # Schedule validation
    │
    ├── services/                # Business logic
    │   ├── orchestrator.py      # Agent coordination
    │   ├── gemini.py            # Gemini AI client
    │   ├── places.py            # Google Places API
    │   ├── weather.py           # OpenWeather API
    │   ├── travel_time.py       # Distance calculation
    │   └── currency.py          # Currency conversion
    │
    └── core/                    # Utilities
        ├── cache.py             # Caching utilities
        ├── exceptions.py        # Custom exceptions
        └── utils.py             # Helper functions
```

## Setup Instructions

### 1. Create Conda Environment

```bash
# Create new conda environment with Python 3.11
conda create -n trip-planner python=3.11 -y

# Activate the environment
conda activate trip-planner
```

### 2. Install Dependencies

```bash
# Navigate to project directory
cd trip-scheduler-agentic-llm

# Install Python packages
pip install -r requirements.txt
```

### 3. Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your API keys
nano .env  # or use any text editor
```

**Required API Keys:**
- `GEMINI_API_KEY` - Get from [Google AI Studio](https://makersuite.google.com/app/apikey)

**Optional API Keys (app works without these using stub data):**
- `OPENWEATHER_API_KEY` - Get from [OpenWeather](https://openweathermap.org/api)
- `GOOGLE_PLACES_API_KEY` - Get from [Google Cloud Console](https://console.cloud.google.com/)
- `DISTANCE_MATRIX_API_KEY` - Same as Google Places or separate key
- `CURRENCY_API_KEY` - Get from [ExchangeRate API](https://exchangerate.host/)

### 4. Initialize Database

```bash
# Run migrations to create database tables
python manage.py migrate

# Create cache table (if not using Redis)
python manage.py createcachetable
```

### 5. Run Development Server

```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000`

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/api/itineraries/` | Queue async generation |
| POST | `/api/itineraries/generate` | Generate itinerary (sync) |
| GET | `/api/itineraries/<id>/` | Get itinerary |
| PATCH | `/api/itineraries/<id>/` | Update itinerary |
| GET | `/api/itineraries/<id>/ics` | Download ICS calendar |
| POST | `/api/analysis/image` | Analyze travel image |
| POST | `/api/edit/block` | Edit schedule block |

## Example Request

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

## Agent Architecture

The system uses 8 specialized agents coordinated by an orchestrator:

1. **ResearchAgent** - Researches accommodation and transport options
2. **PlannerAgent** - Creates day-by-day skeleton plans
3. **WeatherAgent** - Fetches weather and suggests adjustments
4. **AttractionsAgent** - Finds and ranks attractions
5. **SchedulerAgent** - Converts plans to timed schedules
6. **FoodAgent** - Plans meals aligned with schedule
7. **BudgetAgent** - Calculates costs and suggests optimizations
8. **ValidatorAgent** - Validates schedule consistency

## Development

```bash
# Run tests
pytest

# Create superuser for admin
python manage.py createsuperuser

# Access admin at http://localhost:8000/admin/
```

## Production Deployment

1. Set `DJANGO_DEBUG=False`
2. Set a secure `DJANGO_SECRET_KEY`
3. Configure `DATABASE_URL` for PostgreSQL
4. Set `DJANGO_ALLOWED_HOSTS` appropriately
5. Use Gunicorn: `gunicorn trip_planner.wsgi:application`
