
import json
import logging
from typing import Any, Optional

from google import genai
from google.genai import types
from django.conf import settings
from tenacity import retry, stop_after_attempt, wait_exponential

from trip_planner.core.exceptions import GeminiError, GeminiQuotaError
from trip_planner.core.utils import best_effort_json

logger = logging.getLogger(__name__)


class GeminiClient:
    """Client for Google Gemini AI API."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            logger.warning("Gemini API key not configured")
            self.client = None
            self._error_reason = "Gemini API key not configured. Please check your .env file."
            self._initialized = True
            return
        
        try:
            self.client = genai.Client(api_key=api_key)
            self.model_name = settings.GEMINI_MODEL
            # Build list of models to try: Primary -> Fallbacks
            fallback_list = [m.strip() for m in getattr(settings, "GEMINI_FALLBACK_MODELS", []) if m.strip()]
            self.models = [self.model_name] + [m for m in fallback_list if m != self.model_name]
            
            self._initialized = True
            logger.info(f"Gemini initialized with models: {self.models}")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
            self.client = None
            self._error_reason = f"Gemini initialization failed: {str(e)}"
            self._initialized = True
    
    @property
    def is_available(self) -> bool:
        return self.client is not None
    
    def _is_retryable_error(self, e: Exception) -> bool:
        """Check if exception is a 429/quota error."""
        msg = str(e).lower()
        return "429" in msg or "resource_exhausted" in msg or "quota" in msg

    @retry(
        wait=wait_exponential(multiplier=2, min=4, max=60), 
        stop=stop_after_attempt(6), 
        reraise=True
    )
    def generate_content(self, prompt: str, schema: dict = None) -> str:
        """Generate content with optional JSON schema guidance."""
        if not self.is_available:
            raise GeminiError(getattr(self, "_error_reason", "Gemini not available"))
        
        last_exception = None
        
        # Try each model in sequence
        for model in self.models:
            try:
                # Common config
                config = types.GenerateContentConfig(
                    temperature=0.4,
                    response_mime_type="application/json",
                    response_schema=schema,
                ) if schema else types.GenerateContentConfig(
                    temperature=0.4,
                    response_mime_type="application/json",
                )

                response = self.client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=config,
                )
                return response.text or ""
                
            except Exception as e:
                last_exception = e
                is_retryable = self._is_retryable_error(e)
                is_not_found = "not found" in str(e).lower() or "404" in str(e)
                
                # If retryable (quota) OR not found (model invalid), try next model
                if is_retryable or is_not_found:
                    logger.warning(f"Model {model} failed ({e}), trying next fallback...")
                    continue
                
                # Non-retryable error, check schema failure fallback
                if schema:
                     logger.warning(f"Schema-guided generation failed on {model}, retrying without schema: {e}")
                     try:
                        config = types.GenerateContentConfig(temperature=0.4, response_mime_type="application/json")
                        response = self.client.models.generate_content(
                            model=model,
                            contents=prompt,
                            config=config,
                        )
                        return response.text or ""
                     except Exception as inner:
                        # If inner failed, we could try next model, but for simplicity, raise or continue
                        if self._is_retryable_error(inner) or "not found" in str(inner).lower():
                             continue # Continue outer loop
                        raise GeminiError(str(inner))
                
                # If neither retryable nor schema issue, break and raise
                raise GeminiError(str(e))
        
        # If all models failed
        if last_exception:
            if self._is_retryable_error(last_exception):
                 # Logging already done by loop, raise for tenacity
                 raise last_exception 
            raise GeminiError(str(last_exception))
        raise GeminiError("No models available")
    
    def generate_from_image(self, image_bytes: bytes, prompt: str) -> str:
        """Generate content from image using Gemini Vision."""
        if not self.is_available:
            raise GeminiError("Gemini not available")
        
        import PIL.Image
        import io
        
        try:
            image = PIL.Image.open(io.BytesIO(image_bytes))
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[prompt, image]
            )
            return response.text
        except Exception as e:
            raise GeminiError(f"Image analysis failed: {e}")


def render_prompt(system: str, user: str, schema: dict) -> str:
    """Render a complete prompt with schema."""
    schema_json = json.dumps(schema, indent=2)
    return (
        f"{system}\n\n"
        f"USER REQUEST:\n{user}\n\n"
        "Return ONLY valid JSON matching this schema:\n"
        f"{schema_json}\n"
    )


def generate_validated(client: GeminiClient, system_prompt: str, 
                       user_prompt: str, schema: dict) -> tuple[dict, list, list]:
    """Generate and validate JSON content."""
    issues = []
    drafts = []
    
    prompt = render_prompt(system_prompt, user_prompt, schema)
    
    try:
        raw = client.generate_content(prompt, schema)
        drafts.append(raw)
        
        try:
            return best_effort_json(raw), drafts, issues
        except Exception as e:
            issues.append(f"validation_failed: {e}")
        
        # Repair attempt
        repair_prompt = (
            f"Fix this invalid JSON to match the schema:\n{raw}\n\n"
            f"Schema:\n{json.dumps(schema, indent=2)}\n\n"
            "Return ONLY valid JSON."
        )
        repaired = client.generate_content(repair_prompt, schema)
        drafts.append(repaired)
        return best_effort_json(repaired), drafts, issues
        
    except Exception as e:
        if client._is_retryable_error(e):
            raise GeminiQuotaError(f"Gemini Quota Exhausted: {e}")
        issues.append(f"generation_failed: {e}")
        raise GeminiError(f"Failed to generate content: {e}")


# Singleton instance
gemini_client = GeminiClient()
