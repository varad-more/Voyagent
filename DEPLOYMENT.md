# Deployment Guide

## ⚠️ Important Note About GitHub Pages

**GitHub Pages is designed for STATIC websites only.** 

This means it can host HTML, CSS, JavaScript, and images, but it **cannot** run Python, Django, or a database. 

Since **Trip Planner** is a dynamic AI-powered application requiring a Python backend (for Gemini AI, database, etc.), **you cannot deploy the full working application to GitHub Pages.**

However, you *can* use GitHub Pages to host:
1.  Project Documentation
2.  A static landing page showcasing the project
3.  A demo video or screenshots

---

## Part 1: Deploying to Google Cloud Run (Recommended)

Cloud Run is a fully managed serverless platform that runs your containerized app. Your existing `Dockerfile` is already configured for Cloud Run.

### Prerequisites

1.  **Google Cloud Account**: Sign up at [cloud.google.com](https://cloud.google.com) (free tier includes $300 credit)
2.  **gcloud CLI**: Install from [cloud.google.com/sdk](https://cloud.google.com/sdk/docs/install)
3.  **A GCP Project**: Create one in the [Cloud Console](https://console.cloud.google.com)

### Step 1: Authenticate and Set Project

```bash
# Login to Google Cloud
gcloud auth login

# Set your project
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

### Step 2: Deploy

Deploy directly from source (Cloud Build will build the Docker image for you):

```bash
gcloud run deploy trip-planner \
    --source . \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars "DJANGO_DEBUG=False" \
    --set-env-vars "DJANGO_SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(50))')" \
    --set-env-vars "GEMINI_API_KEY=your-gemini-api-key" \
    --set-env-vars "GEMINI_MODEL=gemini-2.0-flash" \
    --set-env-vars "DJANGO_ALLOWED_HOSTS=*" \
    --memory 512Mi \
    --timeout 300
```

> **Note**: Replace `your-gemini-api-key` with your actual Gemini API key. You can add other optional API keys (Places, Weather, etc.) as additional `--set-env-vars` flags.

### Step 3: Set the Service URL

After deploy, Cloud Run will print the service URL (e.g., `https://trip-planner-xxxxx-uc.a.run.app`). Update the deployment with this URL:

```bash
# Get the service URL
SERVICE_URL=$(gcloud run services describe trip-planner --region us-central1 --format 'value(status.url)')

# Update with the service URL for CSRF/ALLOWED_HOSTS
gcloud run services update trip-planner \
    --region us-central1 \
    --set-env-vars "CLOUD_RUN_SERVICE_URL=$SERVICE_URL"
```

### Step 4: Verify

Open the service URL in your browser. You should see the Trip Planner homepage.

```bash
# Open in browser
echo $SERVICE_URL
```

### Adding Optional API Keys

You can update environment variables anytime without rebuilding:

```bash
gcloud run services update trip-planner \
    --region us-central1 \
    --set-env-vars "OPENWEATHER_API_KEY=your-key" \
    --set-env-vars "GOOGLE_PLACES_API_KEY=your-key" \
    --set-env-vars "DISTANCE_MATRIX_API_KEY=your-key" \
    --set-env-vars "CURRENCY_API_KEY=your-key"
```

### Using Secrets (Recommended for Production)

Instead of plain env vars, use Secret Manager for sensitive keys:

```bash
# Create a secret
echo -n "your-gemini-api-key" | gcloud secrets create GEMINI_API_KEY --data-file=-

# Grant Cloud Run access to the secret
gcloud secrets add-iam-policy-binding GEMINI_API_KEY \
    --member="serviceAccount:YOUR_PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

# Deploy with secret reference
gcloud run deploy trip-planner \
    --source . \
    --region us-central1 \
    --set-secrets "GEMINI_API_KEY=GEMINI_API_KEY:latest"
```

### Custom Domain (Optional)

```bash
# Map a custom domain
gcloud run domain-mappings create \
    --service trip-planner \
    --domain your-domain.com \
    --region us-central1
```

### Troubleshooting

| Issue | Solution |
|---|---|
| **403 Forbidden** | Check `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` include your service URL |
| **Static files not loading** | Ensure `whitenoise` is in `requirements.txt` and the middleware is configured |
| **Timeout errors** | Increase `--timeout` (max 3600s) or `--memory` |
| **Cold start slow** | Set `--min-instances 1` to keep one instance warm (costs more) |
| **Data not persisting** | SQLite resets on deploy. Use Cloud SQL for persistent data |

### Cost

Cloud Run's free tier includes:
- **2 million requests/month**
- **360,000 GB-seconds of memory**
- **180,000 vCPU-seconds**

For a personal project, this is more than enough to stay within the free tier.

---

## Part 2: Deploying to Render.com (Alternative)

[Render](https://render.com) is a cloud platform that natively supports Python and Django. It has a free tier.

### 1. Prepare for Deployment
- Ensure `requirements.txt` includes `gunicorn`. (Already done)
- Ensure your `settings.py` reads environment variables (API keys, Debug settings). (Already done)

### 2. Connect to Render
1.  Sign up at [render.com](https://render.com).
2.  Click **New +** and select **Web Service**.
3.  Connect your GitHub repository.

### 3. Configure Service
- **Name:** trip-planner
- **Runtime:** Python 3
- **Build Command:** `pip install -r requirements.txt && python manage.py collectstatic --no-input && python manage.py migrate`
- **Start Command:** `gunicorn trip_planner.wsgi:application`

### 4. Environment Variables
Add the following in the "Environment" tab on Render:
- `PYTHON_VERSION`: `3.11.0`
- `DJANGO_SECRET_KEY`: (Generate a strong random string)
- `DJANGO_DEBUG`: `False`
- `GEMINI_API_KEY`: (Your Gemini API Key)
- `GEMINI_MODEL`: `gemini-2.0-flash`

*Note: SQLite data on Render's free tier is **ephemeral** (resets on every deploy/restart). For persistent data, create a PostgreSQL service on Render.*

---

## Part 3: Deploying Static Landing Page to GitHub Pages

We have set up a GitHub Actions workflow that automatically deploys the content of the `docs/` folder to GitHub Pages.

### Steps:
1.  Ensure you have a `docs/` folder with your static landing page.
2.  Go to your GitHub Repository **Settings**.
3.  Navigate to **Pages** (in the sidebar).
4.  Under **Build and deployment**, select **GitHub Actions** as the source.
5.  Push your changes to the `main` branch.

---

## Part 4: Running with Docker (Locally)

If you have Docker installed, you can run the app without installing Python dependencies on your machine.

```bash
# Build and run
docker-compose up --build
```
The app will be available at `http://localhost:8000`.
