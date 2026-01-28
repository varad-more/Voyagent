from __future__ import annotations

import json
from typing import Any


def extract_json_blob(text: str) -> str | None:
    first = text.find("{")
    last = text.rfind("}")
    if first == -1 or last == -1 or last <= first:
        return None
    return text[first : last + 1]


def try_parse_json(text: str) -> dict[str, Any] | list[Any]:
    return json.loads(text)


def best_effort_json(text: str) -> dict[str, Any] | list[Any]:
    candidate = extract_json_blob(text) or text
    return json.loads(candidate)
