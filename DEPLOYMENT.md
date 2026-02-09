# Deployment Guide

## ⚠️ Important Note About GitHub Pages

**GitHub Pages is designed for STATIC websites only.** 

This means it can host HTML, CSS, JavaScript, and images, but it **cannot** run Python, Django, or a database. 

Since **Trip Planner** is a dynamic AI-powered application requiring a Python backend (for Gemini AI, database, etc.), **you cannot deploy the full working application to GitHub Pages.**

However, you *can* use GitHub Pages to host:
1.  Project Documentation
2.  A static landing page showcasing the project
3.  A demo video or screenshots

This guide covers how to deploy a static landing page to GitHub Pages and how to deploy the *real* application to a platform that supports Python (like Render).

---

## Part 1: Deploying Static Landing Page to GitHub Pages

We have set up a GitHub Actions workflow that automatically deploys the content of the `docs/` folder or a static `index.html` to GitHub Pages.

### Steps:
1.  Ensure you have a `docs/` folder or a simple `index.html` in your repository root (or configured location).
2.  Go to your GitHub Repository **Settings**.
3.  Navigate to **Pages** (in the sidebar).
4.  Under **Build and deployment**, select **GitHub Actions** as the source.
5.  Push your changes to the `main` branch. The workflow will automatically build and deploy.

---

## Part 2: Deploying the Full App (Render.com)

[Render](https://render.com) is a cloud platform that natively supports Python and Django. It has a free tier.

### 1. Prepare for Deployment
- Ensure `requirements.txt` includes `gunicorn`. (Already done)
- Ensure your `settings.py` reads environment variables (API keys, Debug settings). (Already done)
- Create a `build.sh` script in the root directory (optional but recommended for Render commands):

```bash
#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate
```

### 2. Connect to Render
1.  Sign up at [render.com](https://render.com).
2.  Click **New +** and select **Web Service**.
3.  Connect your GitHub repository.

### 3. Configure Service
- **Name:** trip-planner
- **Runtime:** Python 3
- **Build Command:** `./build.sh` (or `pip install -r requirements.txt && python manage.py collectstatic --no-input && python manage.py migrate`)
- **Start Command:** `gunicorn trip_planner.wsgi:application`

### 4. Environment Variables
Add the following in the "Environment" tab on Render:
- `PYTHON_VERSION`: `3.11.0`
- `DJANGO_SECRET_KEY`: (Generate a strong random string)
- `DJANGO_DEBUG`: `False`
- `GEMINI_API_KEY`: (Your Gemini API Key)
- `GEMINI_MODEL`: `gemini-2.0-flash`
- `GOOGLE_PLACES_API_KEY`: (Your Places Key)
- `DISTANCE_MATRIX_API_KEY`: (Your Distance Matrix Key)
- `DATABASE_URL`: (Render creates a PostgreSQL DB for you, or uses internal connection string if you create a Postgres service on Render)

*Note: For the free tier, you might want to use SQLite (which is the default if `DATABASE_URL` is not set), but note that SQLite data on Render's free tier is **ephemeral** (it resets on every deploy/restart). For persistent data, create a "PostgreSQL" service on Render and link it.*

---

## Part 3: Running with Docker (Locally)

If you have Docker installed, you can run the app without installing Python dependencies on your machine.

```bash
# Build and run
docker-compose up --build
```
The app will be available at `http://localhost:8000`.
