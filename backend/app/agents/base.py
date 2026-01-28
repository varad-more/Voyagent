from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.gemini import GeminiClient


@dataclass
class AgentResult:
    data: Any
    drafts: list[str]
    issues: list[str]


class BaseAgent:
    name: str = "base"

    def __init__(self, gemini_client: GeminiClient | None = None) -> None:
        self.gemini_client = gemini_client

    async def run(self, **kwargs):  # pragma: no cover - implemented in subclasses
        raise NotImplementedError
