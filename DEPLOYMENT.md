# Deployment Guide: Hosting for Free

This guide explains how to host the **Voyagent Trip Planner** on a completely free platform stack.

## Recommended Free Stack

We recommend combining **Render.com** (for hosting the Python app) and **Neon.tech** (for the PostgreSQL database). Both offer generous free tiers that don't expire for hobby projects.

- **Web Hosting**: [Render](https://render.com) (Free Web Service)
- **Database**: [Neon](https://neon.tech) (Free PostgreSQL, 0.5GB storage)
- **AI/APIs**: Google Gemini (Free tier), OpenWeatherMap (Free tier)

---

## Step 1: Set up the Database (Neon)

Since Render's free tier files are ephemeral (deleted on restart), you need an external database.

1.  Sign up at [neon.tech](https://neon.tech).
2.  Create a new **Project** (e.g., `trip-planner-db`).
3.  Copy the **Connection String** (Postgres URL). It looks like `postgres://user:pass@ep-rest-123.aws.neon.tech/neondb?sslmode=require`.
4.  Save this URL; you'll need it as your `DATABASE_URL`.

---

## Step 2: Deploy the App (Render)

1.  **Sign up** at [render.com](https://render.com).
2.  Click **New +** and select **Web Service**.
3.  Connect your **GitHub repository**.
4.  Configure the service:
    - **Name**: `trip-planner` (or unique name)
    - **Region**: Choose closest to you (e.g., Ohio, Frankfurt).
    - **Branch**: `main`
    - **Runtime**: `Python 3`
    - **Build Command**: 
      ```bash
      pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
      ```
    - **Start Command**: 
      ```bash
      gunicorn trip_planner.wsgi:application
      ```
    - **Instance Type**: Select **Free**.

---

## Step 3: Configure Environment Variables

Scroll down to the **Environment Variables** section on Render and add the following keys. 

| Key | Value | Description |
|---|---|---|
| `PYTHON_VERSION` | `3.11.0` | Ensures correct Python version |
| `DATABASE_URL` | `postgres://...` | The connection string from Neon (Step 1) |
| `DJANGO_SECRET_KEY` | *(Generate a random string)* | E.g. locally run: `python -c 'import secrets; print(secrets.token_urlsafe(50))'` |
| `DJANGO_DEBUG` | `False` | Important for security |
| `GEMINI_API_KEY` | `...` | Your Google Gemini API Key |
| `GEMINI_MODEL` | `gemini-2.0-flash` | Or your preferred model |
| `OPENWEATHER_API_KEY` | `...` | (Optional) For weather forecasts |
| `GOOGLE_PLACES_API_KEY` | `...` | (Optional) For real place data |
| `CACHE_TTL_ERROR` | `60` | Short cache for errors |

**Note**: For `DJANGO_ALLOWED_HOSTS`, Render automatically sets the hostname, so you typically don't need to set this manually if `settings.py` is configured correctly (it reads `RENDER_EXTERNAL_HOSTNAME` if available, or just set it to `*` for simplicity if debugging). 

*Tip: If you see "DisallowedHost" errors, add `DJANGO_ALLOWED_HOSTS` = `trip-planner.onrender.com` (your app URL).*

---

## Step 4: Finalize and Deploy

1.  Click **Create Web Service**.
2.  Render will start building your app. This takes a few minutes.
3.  Watch the logs. You should see:
    - Dependencies installing...
    - Static files collected...
    - Database migrations applying...
    - `[gunicorn] Listening at: http://0.0.0.0:10000`
4.  Once deployed, clicking the URL at the top will open your live app!

---

## Alternative: Google Cloud Run (Free Tier)

Google Cloud Run has a very generous free tier (2 million requests/mo), but requires a credit card for account setup.

1.  **Install gcloud CLI** and login.
2.  **Deploy**:
    ```bash
    gcloud run deploy trip-planner --source . --allow-unauthenticated --region us-central1
    ```
3.  **Set Environment Variables** via the Cloud Console or CLI.
4.  **Database**: You still need a persistent DB (Cloud SQL is expensive, so use **Neon** here too!).

---

## Troubleshooting

- **Build Fails?** Check logs. Ensure `requirements.txt` is in the root.
- **Application Error?** Check if `DATABASE_URL` is correct. The app crashes if it can't connect to the DB.
- **Static Files Missing?** Ensure the build command includes `collectstatic`.
- **429 Errors (Gemini)?** We implemented retry logic, but the free API has limits. Wait a minute and try again.
