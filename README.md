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

### How to Generate API Keys

#### 1. Google Gemini API (Required)
The application uses Google's Gemini models for all AI reasoning and content generation.

**Setup:**
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey).
2. Click on "Create API key".
3. Select an existing Google Cloud project or create a new one.
4. Copy the generated API key and paste it as `GEMINI_API_KEY` in your `.env` file.
5. Set `GEMINI_MODEL` to one of the supported models (see table below).

**Available Models:**

| Model ID | Description | Best For |
|----------|-------------|----------|
| `gemini-2.0-flash` | Latest, fastest model (Recommended) | General use, best balance of speed and quality |
| `gemini-2.0-flash-lite` | Lightweight version of 2.0 | Lower latency, reduced cost |
| `gemini-2.5-flash` | Next-gen flash model | Advanced reasoning with speed |
| `gemini-2.5-pro` | Most capable model | Complex tasks requiring high accuracy |

> [!NOTE]
> Older models like `gemini-1.5-flash` and `gemini-pro` have been deprecated and may return `404 NOT_FOUND` errors. Use `gemini-2.0-flash` or newer.

**Check Available Models:**

To see all available models and your current configuration:
```bash
python manage.py list_models
```

To validate that your configured model works:
```bash
python manage.py list_models --check
```

#### 2. OpenWeather API (Optional)
Used for real-time weather forecasts logic.
1. Sign up at [OpenWeather](https://openweathermap.org/api).
2. Go to your API keys tab.
3. Generate a new key.
4. Paste it as `OPENWEATHER_API_KEY` in your `.env` file.

#### 3. Google Maps Platform (Optional but Recommended)
Used for retrieving place details (ratings, photos, descriptions) and calculating precise travel times.

**Prerequisites:**
- A Google Cloud Platform (GCP) Account.
- A Billing Account linked to your GCP project (Required by Google, even for free tier).

**Step-by-Step Setup:**

1.  **Create a Project:**
    -   Go to the [Google Cloud Console](https://console.cloud.google.com/).
    -   Click the project dropdown at the top and select **"New Project"**.
    -   Give it a name (e.g., "Trip Planner API") and click **Create**.

2.  **Enable APIs:**
    -   In the sidebar, go to **APIs & Services** > **Library**.
    -   Search for and enable the following **specific** APIs:
        -   **Places API (New)**: *Make sure to select the "New" version if available, or just "Places API". This is used for searching places and fetching details.*
        -   **Distance Matrix API**: *Used to calculate travel times between locations.*
    -   *Note: You may need to enable "Maps JavaScript API" if you plan to extend the frontend with interactive maps later, but it's not strictly required for the current backend logic.*

3.  **Create Credentials:**
    -   Go to **APIs & Services** > **Credentials**.
    -   Click **+ CREATE CREDENTIALS** > **API key**.
    -   Copy the generated key.

4.  **Configure Environment:**
    -   Open your `.env` file.
    -   Paste the key for both variables (unless you want to use separate keys for quota management):
        ```env
        GOOGLE_PLACES_API_KEY=your_api_key_here
        DISTANCE_MATRIX_API_KEY=your_api_key_here
        ```

5.  **Security (Highly Recommended):**
    -   In the Google Cloud Console, click on your newly created API key to edit its settings.
    -   Under **API restrictions**, select **Restrict key**.
    -   Check **Places API** and **Distance Matrix API**. This prevents unauthorized use of your key for other services.
    -   Save changes.

**Troubleshooting:**
-   **"Request Denied" / "Billing Not Enabled":** Ensure your billing account is active and linked to the project.
-   **"API Not Enabled":** Double-check that you enabled the specific APIs listed above in the "Library" section.
-   **Fallbacks:**
    -   If `GOOGLE_PLACES_API_KEY` is missing/invalid, the app uses built-in "stub" (mock) data for attractions and hotels, so you can still test the UI.
    -   If `DISTANCE_MATRIX_API_KEY` is missing/invalid, the app falls back to **OSRM (Open Source Routing Machine)** for travel times, which is free and requires no key.

#### 4. ExchangeRate API (Optional)
Used for currency conversion if you plan trips in different currencies.
1. Go to [ExchangeRate-API](https://www.exchangerate-api.com/).
2. Sign up for a free key.
3. Copy your API key.
4. Paste it as `CURRENCY_API_KEY` in your `.env` file.

**Required API Keys:**
- `GEMINI_API_KEY` - Get from [Google AI Studio](https://makersuite.google.com/app/apikey)

**Optional API Keys (app works without these using stub data):**
- `OPENWEATHER_API_KEY` - Get from [OpenWeather](https://openweathermap.org/api)
- `GOOGLE_PLACES_API_KEY` - Get from [Google Cloud Console](https://console.cloud.google.com/)
- `DISTANCE_MATRIX_API_KEY` - Same as Google Places or separate key
- `CURRENCY_API_KEY` - Get from [ExchangeRate API](https://exchangerate.host/)

- `CURRENCY_API_KEY` - Get from [ExchangeRate API](https://exchangerate.host/)

### Testing API Keys
You can validate your API key configuration using the included test script:

```bash
python manage.py test_keys
```

This command will attempt to make a small request to each configured service and report whether the key is valid, missing, or invalid.

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
