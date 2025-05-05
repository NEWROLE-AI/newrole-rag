import asyncio
import json
from typing import Any

from anthropic import Anthropic, RateLimitError
from aws_lambda_powertools import Logger

from src.application.models.agent_chat_bot import Prompt
from src.application.models.conversation import Message
from src.application.models.vectorized_knowledge import VectorizedKnowledge

from src.application.ports.ai_service import AIService


logger = Logger("ai_service")


class ClaudeAIService(AIService):
    """
    Service for interacting with the Claude AI model via the Anthropic API.

    Attributes:
        _client (Anthropic): The Anthropic API client used to send requests to the Claude model.
    """

    def __init__(
        self,
        client: Anthropic,
        temperature: int,
        max_tokens: int,
        system_prompt: str,
        max_retries: int = 3,
        initial_wait: float = 1.0,
        max_wait: float = 60.0,
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
        self._max_retries = max_retries
        self._initial_wait = initial_wait
        self._max_wait = max_wait

    async def _exponential_backoff(self, attempt: int) -> float:
        """
        Calculate exponential backoff time with jitter.

        Args:
            attempt (int): Current retry attempt number.

        Returns:
            float: Wait time in seconds.
        """
        wait_time = min(self._max_wait, self._initial_wait * (2 ** (attempt - 1)))
        # Add random jitter to prevent thundering herd problem
        jitter = wait_time * random.uniform(0.5, 1.5)
        return jitter

    async def generate_response(
        self,
        prompt: Prompt,
        vectorized_knowledge_base: VectorizedKnowledge,
        messages: list[Message],
    ) -> tuple[str, dict[str, Any]]:
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
            f"IMPORTANT: Always response ONLY in JSON format with the following structure:\n"
            "{\n"
            f" ‘message’: ‘Your text reply to the person’, \n"
            " ‘payload’: {'data_ready': false/true, [other data]}\n"
            "}\n"
            f"reponse_format: json"
            f"After passing background checkin add json with results and flag in payload that checkin passed data_ready: bool"
            f"No additional words or text outside of JSON. Always use the correct JSON format."
        )
        logger.info(system_prompt)
        for attempt in range(1, self._max_retries + 1):
            try:
                response = self._client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=self._max_tokens,
                    temperature=self._temperature,
                    system=system_prompt,
                    messages=[message.to_dict_ai() for message in messages],
                )
                logger.info(response)

                try:
                    response_json = json.loads(response.content[0].text)
                    logger.info(response_json.get("payload"))
                    return (
                        response_json.get("message", ""),
                        response_json.get("payload", {}),
                    )
                except json.JSONDecodeError:
                    # Fallback if JSON parsing fails
                    return (
                        response.content[0].text,
                        {"error": "Could not parse JSON response"},
                    )

            except RateLimitError as e:
                logger.warning(f"Rate limit encountered (attempt {attempt}): {str(e)}")

                if attempt == self._max_retries:
                    logger.error("Max retries reached. Raising exception.")
                    raise

                # Calculate exponential backoff time
                wait_time = await self._exponential_backoff(attempt)
                logger.info(f"Waiting {wait_time:.2f} seconds before retry")

                await asyncio.sleep(wait_time)

            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                raise
