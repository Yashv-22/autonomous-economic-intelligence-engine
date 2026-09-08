"""
Model Gateway Base Interface and Data Structures.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from src.models.schemas import ModelResponse, TokenUsage


class ModelMessage(BaseModel):
    """Chat message structure."""
    role: str  # "system", "user", "assistant"
    content: str


class BaseModelProvider(ABC):
    """Abstract base class for all LLM model providers."""

    name: str

    @abstractmethod
    def generate(
        self,
        messages: List[ModelMessage],
        model: str,
        temperature: float = 0.0,
        max_tokens: int = 2048,
        **kwargs
    ) -> ModelResponse:
        """Send prompt to provider and return standardized ModelResponse."""
        pass
