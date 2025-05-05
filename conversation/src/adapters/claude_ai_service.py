from anthropic import Anthropic

from src.application.models.agent_chat_bot import Prompt
from src.application.models.conversation import Message
from src.application.models.vectorized_knowledge import VectorizedKnowledge

from src.application.ports.ai_service import AIService


class ClaudeAIService(AIService):
    """
    Service for interacting with the Claude AI model via the Anthropic API.

    Attributes:
        _client (Anthropic): The Anthropic API client used to send requests to the Claude model.
    """

    def __init__(
        self, client: Anthropic, temperature: int, max_tokens: int, system_prompt: str
    ):
        """
        Initializes the Claude AI service with the provided Anthropic client.

        Args:
            client (Anthropic): The Anthropic API client.
            temperature (int): The temperature of the system.
            max_tokens (int): The maximum number of tokens in the system.
            system_prompt (str): The system prompt.
        """
        self._client = client
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._system_prompt = system_prompt

    async def generate_response(
        self,
        prompt: Prompt,
        vectorized_knowledge_base: VectorizedKnowledge,
        messages: list[Message],
    ) -> str:
        """
        Generates a response from Claude AI based on the provided prompt, vectorized knowledge, and message history.

        Args:
            prompt (Prompt): The prompt to give Claude AI.
            vectorized_knowledge_base (VectorizedKnowledge): The knowledge base related to the conversation.
            messages (list[Message]): The message history for context.

        Returns:
            str: The generated response from Claude AI.
        """
        system_prompt = (
            f"{prompt.text}\n\n"
            f"{self._system_prompt}\n"
            f"{[f"Resource: {resource.resource_id} Content: {resource.content}\n" for resource in vectorized_knowledge_base.resources]}"
        )
        response = self._client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=self._max_tokens,
            temperature=self._temperature,
            system=system_prompt,
            messages=[message.to_dict_ai() for message in messages],
        )
        return response.content[0].text
