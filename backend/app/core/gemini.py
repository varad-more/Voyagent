from __future__ import annotations

import json
from typing import Any, TypeVar

import google.generativeai as genai
import structlog
from pydantic import BaseModel, ValidationError
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.utils.json_repair import best_effort_json


logger = structlog.get_logger(__name__)
ModelT = TypeVar("ModelT", bound=BaseModel)


class GeminiClient:
    def __init__(self) -> None:
        settings = get_settings()
        if not settings.gemini_api_key:
            raise RuntimeError("Gemini API key is not configured")
        genai.configure(api_key=settings.gemini_api_key)
        self.model = genai.GenerativeModel(settings.gemini_model)

    @retry(wait=wait_exponential(multiplier=1, min=2, max=8), stop=stop_after_attempt(3))
    def generate_content(self, prompt: str, schema: dict[str, Any]) -> str:
        response = self.model.generate_content(
            prompt,
            generation_config={
                "response_mime_type": "application/json",
                "response_schema": schema,
                "temperature": 0.4,
            },
        )
        return response.text or ""


def build_schema_from_model(model: type[BaseModel]) -> dict[str, Any]:
    return model.model_json_schema()


def render_prompt(system: str, user: str, schema: dict[str, Any]) -> str:
    schema_json = json.dumps(schema, ensure_ascii=True, indent=2)
    return (
        f"{system}\n\n"
        f"USER REQUEST:\n{user}\n\n"
        "Return ONLY valid JSON that matches this schema.\n"
        f"SCHEMA:\n{schema_json}\n"
    )


def repair_prompt(bad_json: str, schema: dict[str, Any]) -> str:
    schema_json = json.dumps(schema, ensure_ascii=True, indent=2)
    return (
        "You will be given invalid JSON. Fix it to match the schema exactly.\n"
        "Return ONLY valid JSON.\n\n"
        f"INVALID JSON:\n{bad_json}\n\n"
        f"SCHEMA:\n{schema_json}\n"
    )


def generate_validated(
    *,
    client: GeminiClient,
    system_prompt: str,
    user_prompt: str,
    model_cls: type[ModelT],
) -> tuple[ModelT, list[str], list[str]]:
    issues: list[str] = []
    drafts: list[str] = []
    schema = build_schema_from_model(model_cls)

    raw = client.generate_content(render_prompt(system_prompt, user_prompt, schema), schema)
    drafts.append(raw)
    try:
        data = best_effort_json(raw)
        return model_cls.model_validate(data), drafts, issues
    except (ValidationError, json.JSONDecodeError) as exc:
        issues.append(f"initial_validation_failed: {exc}")

    repaired = client.generate_content(repair_prompt(raw, schema), schema)
    drafts.append(repaired)
    data = best_effort_json(repaired)
    return model_cls.model_validate(data), drafts, issues
