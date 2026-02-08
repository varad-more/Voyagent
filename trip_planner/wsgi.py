"""WSGI config for Trip Planner."""
import os
from django.core.wsgi import get_wsgi_application

# Load .env file
try:
    import dotenv
    dotenv.load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
except ImportError:
    pass

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "trip_planner.settings")
application = get_wsgi_application()
