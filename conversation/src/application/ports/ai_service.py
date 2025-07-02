from abc import ABC, abstractmethod
from typing import Any

from src.application.models.agent_chat_bot import Prompt
from src.application.models.conversation import Message
from src.application.models.vectorized_knowledge import VectorizedKnowledge


class AIService(ABC):
    """
    Interface for the AI service to generate responses based on conversation and knowledge base.

    Methods:
        generate_response: Generates a response based on the provided prompt, knowledge base, and conversation.
    """

    @abstractmethod
    async def generate_response(
        self,
        prompt: Prompt,
        vectorized_knowledge_base: list[dict],
        messages: list[Message],
    ) -> tuple[str, dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    async def generate_sql_response(
        self,
        query: str
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    async def generate_api_response(
            self,
            messages: list[Message],
            knowledge_base_id: str,
            resource_info: dict,
    ) -> dict:
        raise NotImplementedError

    @abstractmethod
    async def generate_response_with_resources(
            self,
            prompt: Prompt,
            resource_data: dict,
            messages: list[Message],
    )-> str:
        raise NotImplementedError