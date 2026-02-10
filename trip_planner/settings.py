"""
Django settings for Voyagent (AI-Powered Trip Planning).
"""
import os
from pathlib import Path

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Security
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-change-this-in-production"
)
DEBUG = os.environ.get("DJANGO_DEBUG", "True").lower() == "true"
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,0.0.0.0").split(",")

# Cloud Run: Allow the service URL (*.run.app)
CLOUD_RUN_SERVICE_URL = os.environ.get("CLOUD_RUN_SERVICE_URL", "")
if CLOUD_RUN_SERVICE_URL:
    from urllib.parse import urlparse
    cloud_host = urlparse(CLOUD_RUN_SERVICE_URL).hostname or CLOUD_RUN_SERVICE_URL
    ALLOWED_HOSTS.append(cloud_host)

# Initialize CSRF trusted origins
CSRF_TRUSTED_ORIGINS = []

# Render: Automatic configuration
if os.environ.get("RENDER"):
    ALLOWED_HOSTS.append(".onrender.com")
    render_hostname = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
    if render_hostname:
        ALLOWED_HOSTS.append(render_hostname)
        CSRF_TRUSTED_ORIGINS.append(f"https://{render_hostname}")

# Cloud Run terminates TLS at the load balancer
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# CSRF env var integration
if os.environ.get("CSRF_TRUSTED_ORIGINS"):
    CSRF_TRUSTED_ORIGINS.extend(os.environ.get("CSRF_TRUSTED_ORIGINS").split(","))

if CLOUD_RUN_SERVICE_URL:
    CSRF_TRUSTED_ORIGINS.append(CLOUD_RUN_SERVICE_URL)
    
CSRF_TRUSTED_ORIGINS = [o for o in CSRF_TRUSTED_ORIGINS if o]  # remove empty strings

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "corsheaders",
    # Local
    "trip_planner",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # Serve static files in production
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "trip_planner.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "trip_planner" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "trip_planner.wsgi.application"

# Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Use PostgreSQL if DATABASE_URL is set
database_url = os.environ.get("DATABASE_URL")
if database_url:
    import dj_database_url
    DATABASES["default"] = dj_database_url.config(default=database_url)

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [
    BASE_DIR / "trip_planner" / "static",
]

# WhiteNoise: Compress and cache static files in production
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Default primary key
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# REST Framework
REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.MultiPartParser",
        "rest_framework.parsers.FormParser",
    ],
    "EXCEPTION_HANDLER": "trip_planner.core.exceptions.custom_exception_handler",
}

# CORS
CORS_ALLOW_ALL_ORIGINS = DEBUG
CORS_ALLOW_CREDENTIALS = True

# =============================================================================
# Trip Planner Configuration
# =============================================================================

# API Keys
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.0-flash")
GEMINI_FALLBACK_MODELS = os.environ.get("GEMINI_FALLBACK_MODELS", "gemini-2.0-flash,gemini-1.5-flash,gemini-1.5-flash-8b").split(",")
OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY", "")
GOOGLE_PLACES_API_KEY = os.environ.get("GOOGLE_PLACES_API_KEY", "")
DISTANCE_MATRIX_API_KEY = os.environ.get("DISTANCE_MATRIX_API_KEY", "")
CURRENCY_API_KEY = os.environ.get("CURRENCY_API_KEY", "")

# Cache Configuration
REDIS_URL = os.environ.get("REDIS_URL", "")

# Cache TTLs (seconds)
CACHE_TTL_WEATHER = int(os.environ.get("CACHE_TTL_WEATHER", "3600"))      # 1 hour
CACHE_TTL_PLACES = int(os.environ.get("CACHE_TTL_PLACES", "86400"))       # 24 hours
CACHE_TTL_TRAVEL = int(os.environ.get("CACHE_TTL_TRAVEL", "3600"))        # 1 hour
CACHE_TTL_CURRENCY = int(os.environ.get("CACHE_TTL_CURRENCY", "43200"))   # 12 hours
CACHE_TTL_ERROR = int(os.environ.get("CACHE_TTL_ERROR", "60"))            # 1 minute (for failures)

# Planner
PLANNER_BUFFER_MINUTES = int(os.environ.get("PLANNER_BUFFER_MINUTES", "20"))

# Redis Cache (optional)
if REDIS_URL:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": REDIS_URL,
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.db.DatabaseCache",
            "LOCATION": "cache_table",
        }
    }

# Logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "trip_planner": {
            "handlers": ["console"],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": False,
        },
        # Suppress verbose GenAI logs (like AFC enabled)
        "google": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "models": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}
