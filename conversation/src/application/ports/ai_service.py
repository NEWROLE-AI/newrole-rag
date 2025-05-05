from abc import ABC, abstractmethod

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
        vectorized_knowledge_base: VectorizedKnowledge,
        messages: list[Message],
    ) -> str:
        raise NotImplementedError
