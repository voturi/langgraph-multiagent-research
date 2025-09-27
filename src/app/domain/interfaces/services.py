"""Domain service interfaces."""

from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, List

from ..models.value_objects import ExecutionResult


class LLMService(ABC):
    """Abstract interface for LLM services."""

    @abstractmethod
    async def generate_response(
        self,
        messages: List[Dict[str, Any]],
        model: str = None,
        temperature: float = 0.1,
        max_tokens: int = 1000,
        **kwargs,
    ) -> ExecutionResult:
        """Generate a response from messages."""
        pass

    @abstractmethod
    async def generate_streaming(
        self,
        messages: List[Dict[str, Any]],
        model: str = None,
        temperature: float = 0.1,
        max_tokens: int = 1000,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """Generate streaming response."""
        pass

    @abstractmethod
    async def embed_text(self, text: str, model: str = None) -> ExecutionResult:
        """Generate text embeddings."""
        pass

    @abstractmethod
    def get_available_models(self) -> List[str]:
        """Get list of available models."""
        pass