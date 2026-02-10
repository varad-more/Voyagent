#!/bin/bash
set -e

# Run database migrations (initializes SQLite on first start)
echo "Running migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start gunicorn
# Cloud Run injects PORT env var (default 8080)
PORT=${PORT:-8080}
echo "Starting gunicorn on port $PORT..."
exec gunicorn trip_planner.wsgi:application \
    --bind "0.0.0.0:$PORT" \
    --workers 2 \
    --threads 4 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
