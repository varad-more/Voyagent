from django.core.management.base import BaseCommand
from django.conf import settings
import requests
import json

class Command(BaseCommand):
    help = 'Test configured API keys by making sample requests'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.MIGRATE_HEADING('Testing API Keys...'))

        # 1. Google Gemini API
        self.stdout.write('Checking Google Gemini API Key...')
        if not settings.GEMINI_API_KEY:
            self.stdout.write(self.style.WARNING('  [SKIPPED] GEMINI_API_KEY not configured'))
        else:
            try:
                from google import genai
                from google.genai import types
                
                # Check for model configuration
                model_name = getattr(settings, 'GEMINI_MODEL', 'gemini-2.0-flash')
                self.stdout.write(f"  Attempting to use model: {model_name}")
                
                client = genai.Client(api_key=settings.GEMINI_API_KEY)
                response = client.models.generate_content(
                    model=model_name,
                    contents='Hello, are you working?'
                )
                if response.text:
                    self.stdout.write(self.style.SUCCESS(f'  [SUCCESS] Gemini API is working (Model: {model_name})'))
                else:
                    self.stdout.write(self.style.ERROR('  [FAILED] Gemini API returned empty response'))
                    
            except ImportError:
                self.stdout.write(self.style.ERROR('  [FAILED] google-genai library not found. Please install requirements.txt'))
            except Exception as e:
                error_msg = str(e)
                if "404" in error_msg:
                    self.stdout.write(self.style.ERROR(f'  [FAILED] Model {model_name} not found or not supported. Check GEMINI_MODEL in .env'))
                elif "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                    self.stdout.write(self.style.WARNING(f'  [WARNING] Quota exceeded for model {model_name}. API key is valid but rate limited.'))
                else:
                    self.stdout.write(self.style.ERROR(f'  [FAILED] Gemini API error: {e}'))

        # 2. OpenWeather API
        self.stdout.write('\nChecking OpenWeather API Key...')
        if not settings.OPENWEATHER_API_KEY:
            self.stdout.write(self.style.WARNING('  [SKIPPED] OPENWEATHER_API_KEY not configured'))
        else:
            try:
                url = f"https://api.openweathermap.org/data/2.5/weather?q=Phoenix&appid={settings.OPENWEATHER_API_KEY}"
                resp = requests.get(url, timeout=5)
                if resp.status_code == 200:
                    self.stdout.write(self.style.SUCCESS('  [SUCCESS] OpenWeather API is working'))
                else:
                    self.stdout.write(self.style.ERROR(f'  [FAILED] OpenWeather API returned {resp.status_code}: {resp.text}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  [FAILED] OpenWeather API error: {e}'))

        # 3. Google Places API
        self.stdout.write('\nChecking Google Places API Key...')
        key = getattr(settings, 'GOOGLE_PLACES_API_KEY', None)
        if not key:
            self.stdout.write(self.style.WARNING('  [SKIPPED] GOOGLE_PLACES_API_KEY not configured'))
        else:
            try:
                url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query=Grand+Canyon&key={key}"
                resp = requests.get(url, timeout=5)
                data = resp.json()
                if resp.status_code == 200 and data.get('status') == 'OK':
                    self.stdout.write(self.style.SUCCESS('  [SUCCESS] Google Places API is working'))
                elif resp.status_code == 200:
                     self.stdout.write(self.style.ERROR(f"  [FAILED] Google Places API returned: {data.get('status')} - {data.get('error_message')}"))
                else:
                    self.stdout.write(self.style.ERROR(f'  [FAILED] Google Places API returned {resp.status_code}: {resp.text}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  [FAILED] Google Places API error: {e}'))

        # 4. Google Distance Matrix API
        self.stdout.write('\nChecking Google Distance Matrix API Key...')
        key = getattr(settings, 'DISTANCE_MATRIX_API_KEY', None)
        if not key:
            self.stdout.write(self.style.WARNING('  [SKIPPED] DISTANCE_MATRIX_API_KEY not configured'))
        else:
            try:
                url = f"https://maps.googleapis.com/maps/api/distancematrix/json?origins=Phoenix&destinations=Tucson&key={key}"
                resp = requests.get(url, timeout=5)
                data = resp.json()
                if resp.status_code == 200 and data.get('status') == 'OK':
                     self.stdout.write(self.style.SUCCESS('  [SUCCESS] Google Distance Matrix API is working'))
                elif resp.status_code == 200:
                     self.stdout.write(self.style.ERROR(f"  [FAILED] Google Distance Matrix API returned: {data.get('status')} - {data.get('error_message')}"))
                else:
                    self.stdout.write(self.style.ERROR(f'  [FAILED] Google Distance Matrix API returned {resp.status_code}: {resp.text}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  [FAILED] Google Distance Matrix API error: {e}'))

        # 5. ExchangeRate API
        self.stdout.write('\nChecking ExchangeRate API Key...')
        key = getattr(settings, 'CURRENCY_API_KEY', None)
        if not key:
            self.stdout.write(self.style.WARNING('  [SKIPPED] CURRENCY_API_KEY not configured'))
        else:
            try:
                url = f"https://v6.exchangerate-api.com/v6/{key}/latest/USD"
                resp = requests.get(url, timeout=5)
                if resp.status_code == 200:
                    self.stdout.write(self.style.SUCCESS('  [SUCCESS] ExchangeRate API is working'))
                else:
                    self.stdout.write(self.style.ERROR(f'  [FAILED] ExchangeRate API returned {resp.status_code}: {resp.text}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  [FAILED] ExchangeRate API error: {e}'))
