"""
Base agent class.
"""
from dataclasses import dataclass, field
from typing import Any, Optional
from abc import ABC, abstractmethod


@dataclass
class AgentResult:
    """Result from agent execution."""
    data: Any
    drafts: list[str] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)


class BaseAgent(ABC):
    """Abstract base class for all agents."""
    name: str = "base"
    
    def __init__(self, gemini_client=None):
        self.gemini_client = gemini_client
    
    @property
    def has_ai(self) -> bool:
        return self.gemini_client is not None and self.gemini_client.is_available
    
    @abstractmethod
    def run(self, **kwargs) -> AgentResult:
        raise NotImplementedError
    
    def _stub_result(self, data: Any, issue: str = "gemini_disabled") -> AgentResult:
        return AgentResult(data=data, drafts=[], issues=[issue])
