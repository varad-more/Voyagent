from django.core.management.base import BaseCommand
from django.conf import settings


# Known available Gemini models (as of Feb 2026)
KNOWN_MODELS = {
    'Flash Models (Fast)': [
        'gemini-2.0-flash',
        'gemini-2.0-flash-lite',
        'gemini-2.5-flash',
        'gemini-2.5-flash-lite',
    ],
    'Pro Models (Powerful)': [
        'gemini-2.5-pro',
        'gemini-3-pro-preview',
    ],
    'Experimental': [
        'gemini-3-flash-preview',
        'gemini-exp-1206',
    ],
}


class Command(BaseCommand):
    help = 'List available Gemini models and validate current configuration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--check',
            action='store_true',
            help='Validate that the configured model works',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('Gemini Model Configuration'))
        self.stdout.write('')
        
        # Show known models
        self.stdout.write(self.style.SUCCESS('Known Available Models:'))
        self.stdout.write('')
        
        for category, models in KNOWN_MODELS.items():
            self.stdout.write(f'  {category}:')
            for model in models:
                marker = ' *' if model == settings.GEMINI_MODEL else ''
                self.stdout.write(f'    - {model}{marker}')
            self.stdout.write('')
        
        self.stdout.write(self.style.WARNING(f'Currently configured: {settings.GEMINI_MODEL}'))
        
        if settings.GEMINI_MODEL not in [m for models in KNOWN_MODELS.values() for m in models]:
            self.stdout.write(self.style.WARNING(f'  Note: {settings.GEMINI_MODEL} is not in known models list'))
        
        # Validate if requested
        if options['check']:
            self.stdout.write('')
            self.stdout.write('Validating configured model...')
            
            if not settings.GEMINI_API_KEY:
                self.stdout.write(self.style.ERROR('  GEMINI_API_KEY not configured'))
                return
            
            try:
                from google import genai
                client = genai.Client(api_key=settings.GEMINI_API_KEY)
                response = client.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    contents='Hello'
                )
                if response.text:
                    self.stdout.write(self.style.SUCCESS(f'  [VALID] Model {settings.GEMINI_MODEL} is working!'))
                else:
                    self.stdout.write(self.style.ERROR('  [INVALID] Model returned empty response'))
            except Exception as e:
                error_msg = str(e)
                if '404' in error_msg:
                    self.stdout.write(self.style.ERROR(f'  [INVALID] Model {settings.GEMINI_MODEL} not found'))
                elif '429' in error_msg or 'RESOURCE_EXHAUSTED' in error_msg:
                    self.stdout.write(self.style.WARNING(f'  [RATE LIMITED] Model exists but quota exceeded'))
                else:
                    self.stdout.write(self.style.ERROR(f'  [ERROR] {e}'))
        else:
            self.stdout.write('')
            self.stdout.write('Run with --check to validate configured model')
