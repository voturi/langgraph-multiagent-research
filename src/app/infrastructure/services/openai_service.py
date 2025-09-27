"""OpenAI service implementation"""

import logging
import os
from typing import Any, AsyncGenerator, Dict, List, Optional

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from ...domain.interfaces.services import LLMService
from ...domain.models.value_objects import ExecutionResult

logger = logging.getLogger(__name__)


class OpenAIService(LLMService):
    """OpenAI implementation of LLM service"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        default_model: str = "gpt-4o-mini",
        base_url: Optional[str] = None,
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.default_model = default_model
        self.base_url = base_url

        if not self.api_key:
            raise ValueError(
                "OpenAI API key is required. Set OPENAI_API_KEY environment variable "
                "or pass api_key parameter"
            )

        self._chat_client = ChatOpenAI(
            api_key=self.api_key, model=self.default_model, base_url=self.base_url
        )

        self._embedding_client = OpenAIEmbeddings(
            api_key=self.api_key, base_url=self.base_url
        )

        logger.info(f"Initialized OpenAI service with model: {self.default_model}")

    def _convert_messages(self, messages: List[Dict[str, Any]]) -> List:
        """Convert message dicts to LangChain message objects"""
        langchain_messages = []

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                langchain_messages.append(SystemMessage(content=content))
            elif role == "assistant":
                langchain_messages.append(AIMessage(content=content))
            else:  # user or any other role
                langchain_messages.append(HumanMessage(content=content))

        return langchain_messages

    async def generate_response(
        self,
        messages: List[Dict[str, Any]],
        model: str = None,
        temperature: float = 0.1,
        max_tokens: int = 1000,
        **kwargs,
    ) -> ExecutionResult:
        """Generate response from messages"""
        try:
            current_model = model or self.default_model

            chat_client = self._chat_client
            if model and model != self.default_model:
                chat_client = ChatOpenAI(
                    api_key=self.api_key,
                    model=current_model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    base_url=self.base_url,
                    **kwargs,
                )
            else:
                chat_client.temperature = temperature
                chat_client.max_tokens = max_tokens

            langchain_messages = self._convert_messages(messages)

            logger.info(
                f"Generating response with {current_model} for {len(messages)} messages"
            )
            response = await chat_client.ainvoke(langchain_messages)

            return ExecutionResult(
                success=True,
                data={
                    "response": response.content,
                    "model": current_model,
                    "usage": getattr(response, "usage_metadata", {}),
                    "message_count": len(messages),
                },
                metadata={
                    "provider": "openai",
                    "model": current_model,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )

        except Exception as e:
            logger.error(f"Error generating OpenAI response: {str(e)}")
            return ExecutionResult(
                success=False,
                error=str(e),
                metadata={
                    "provider": "openai",
                    "model": model or self.default_model,
                    "error_type": type(e).__name__,
                },
            )

    async def generate_streaming(
        self,
        messages: List[Dict[str, Any]],
        model: str = None,
        temperature: float = 0.1,
        max_tokens: int = 1000,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """Generate streaming response"""
        try:
            current_model = model or self.default_model

            chat_client = ChatOpenAI(
                api_key=self.api_key,
                model=current_model,
                temperature=temperature,
                max_tokens=max_tokens,
                streaming=True,
                base_url=self.base_url,
                **kwargs,
            )

            langchain_messages = self._convert_messages(messages)

            logger.info(f"Starting streaming response with {current_model}")

            async for chunk in chat_client.astream(langchain_messages):
                if chunk.content:
                    yield chunk.content

        except Exception as e:
            logger.error(f"Error in streaming response: {str(e)}")
            yield f"Error: {str(e)}"

    async def embed_text(self, text: str, model: str = None) -> ExecutionResult:
        """Generate text embeddings"""
        try:
            embeddings = await self._embedding_client.aembed_query(text)

            return ExecutionResult(
                success=True,
                data={
                    "embeddings": embeddings,
                    "text_length": len(text),
                    "embedding_dim": len(embeddings) if embeddings else 0,
                },
                metadata={"provider": "openai", "model": "text-embedding-3-small"},
            )

        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            return ExecutionResult(
                success=False,
                error=str(e),
                metadata={"provider": "openai", "error_type": type(e).__name__},
            )

    def get_available_models(self) -> List[str]:
        """Get list of available OpenAI models"""
        return [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k",
        ]
