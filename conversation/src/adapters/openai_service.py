import asyncio
import json
import random
from datetime import datetime, timezone
from typing import Any

import tiktoken
from openai import AsyncOpenAI, RateLimitError
from aws_lambda_powertools import Logger

from src.application.models.agent_chat_bot import Prompt
from src.application.models.conversation import Message
from src.application.models.vectorized_knowledge import VectorizedKnowledge
from src.application.ports.ai_service import AIService

logger = Logger("ai_service")


class OpenAIService(AIService):
    """
    Service for interacting with the GPT-4 model via the OpenAI API.

    Attributes:
        _client (AsyncOpenAI): The OpenAI API client used to send requests to the GPT-4 model.
    """

    def __init__(
            self,
            client: AsyncOpenAI,
            temperature: float,
            max_tokens: int,
            system_prompt: str,
            max_retries: int = 3,
            initial_wait: float = 0.5,
            max_wait: float = 60.0,
            max_context_length: int = 128000,
            schema: str = "",
            sql_prompt: str = ""
    ):
        """
        Initializes the GPT-4 AI service with the provided OpenAI client.

        Args:
            client (AsyncOpenAI): The OpenAI API client.
            temperature (float): The temperature parameter for response generation.
            max_tokens (int): The maximum number of tokens in the response.
            system_prompt (str): The system prompt.
            max_retries (int): Maximum number of retry attempts.
            initial_wait (float): Initial wait time for exponential backoff.
            max_wait (float): Maximum wait time for exponential backoff.
        """
        self._client = client
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._system_prompt = system_prompt
        self._max_retries = max_retries
        self._initial_wait = initial_wait
        self._max_wait = max_wait
        self._max_context_length = max_context_length
        self._encoding = tiktoken.encoding_for_model("gpt-4")
        self._schema = schema
        self.sql_prompt = sql_prompt

    def _count_tokens(self, text: str) -> int:
        """Count the number of tokens in a text string."""
        return len(self._encoding.encode(text))

    def _prepare_messages_with_token_limit(
            self,
            prompt: Prompt,
            vectorized_knowledge_base: list[dict],
            messages: list[Message],
    ) -> list[dict[str, str]]:
        """
        Prepare messages while respecting token limits by trimming knowledge base resources if needed.
        """
        system_prompt_template = (
            f"{prompt.text}\n\n"
            f"{self._system_prompt}\n"
        )

        # Calculate tokens for fixed content
        system_prompt_tokens = self._count_tokens(system_prompt_template)
        message_tokens = sum(self._count_tokens(msg.content) for msg in messages[-15:])

        # Calculate available tokens for knowledge base
        reserved_tokens = 5000  # Reserve some tokens for response
        available_tokens = self._max_context_length - system_prompt_tokens - message_tokens - reserved_tokens

        # Prepare knowledge base content while respecting token limit
        knowledge_base_content = []
        total_kb_tokens = 0

        for resource in vectorized_knowledge_base:
            resource_content = f'Resource: {resource}\n'
            resource_tokens = self._count_tokens(resource_content)

            if total_kb_tokens + resource_tokens <= available_tokens:
                knowledge_base_content.append(resource_content)
                total_kb_tokens += resource_tokens
            else:
                logger.warning(f"Skipping resource {resource} due to token limit")
                break

        # Combine system prompt with knowledge base content
        final_system_prompt = system_prompt_template + '\n'.join(knowledge_base_content)

        # Prepare final message list
        formatted_messages = [
            {"role": "system", "content": final_system_prompt},
            *[
                 {
                     "role": msg.role,
                     "content": msg.content
                 }
                 for msg in messages
             ][-15:]
        ]

        return formatted_messages

    async def _exponential_backoff(self, attempt: int) -> float:
        """
        Calculate exponential backoff time with jitter.

        Args:
            attempt (int): Current retry attempt number.

        Returns:
            float: Wait time in seconds.
        """
        wait_time = min(self._max_wait, self._initial_wait * (2 ** (attempt - 1)))
        jitter = wait_time * random.uniform(0.5, 1.5)
        return jitter

    async def generate_response(
            self,
            prompt: Prompt,
            vectorized_knowledge_base: list[dict],
            messages: list[Message],
    ) -> tuple[str, dict[str, Any]]:
        """
        Generates a response from GPT-4 based on the provided prompt, vectorized knowledge, and message history.

        Args:
            prompt (Prompt): The prompt to give GPT-4.
            vectorized_knowledge_base (VectorizedKnowledge): The knowledge base related to the conversation.
            messages (list[Message]): The message history for context.

        Returns:
            tuple[str, dict[str, Any]]: The generated response message and payload.

        Raises:
            Exception: If the API request fails after max retries or other errors occur.
        """
        formatted_messages = self._prepare_messages_with_token_limit(
            prompt, vectorized_knowledge_base, messages
        )
        logger.info(formatted_messages)

        for attempt in range(1, self._max_retries + 1):
            try:
                logger.info(datetime.now(timezone.utc))
                response = await self._client.chat.completions.create(
                    model="gpt-4o",  # Using the latest GPT-4 Turbo model
                    messages=formatted_messages,
                    temperature=self._temperature,
                    max_tokens=self._max_tokens,
                    response_format={"type": "json_object"}
                )
                logger.info(datetime.now(timezone.utc))
                logger.info("API Response:", extra={"response": response})

                try:
                    response_content = response.choices[0].message.content
                    response_json = json.loads(response_content)
                    message = response_json.get("message", "")
                    cleaned_message = message.replace("**", "")  # Remove '**' symbols
                    response_json["message"] = cleaned_message

                    logger.info(response_json.get("payload"))
                    return (
                        response_json.get("message", ""),
                        response_json.get("payload", {})
                    )
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse JSON response: {response}")
                    return (
                        response.choices[0].message.content,
                        {"error": "Could not parse JSON response"}
                    )

            except RateLimitError as e:
                logger.warning(f"Rate limit encountered (attempt {attempt}): {str(e)}")

                if attempt == self._max_retries:
                    logger.error("Max retries reached. Raising exception.")
                    raise

                wait_time = await self._exponential_backoff(attempt)
                logger.info(f"Waiting {wait_time:.2f} seconds before retry")
                await asyncio.sleep(wait_time)

            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                raise

    async def generate_sql_response(self, query: str) -> str:
        system_prompt = f"""{self.sql_prompt}
        {self._schema}
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]
        for attempt in range(1, self._max_retries + 1):
            try:
                logger.info(datetime.now(timezone.utc))
                response = await self._client.chat.completions.create(
                    model="gpt-4o",  # Using the latest GPT-4 Turbo model
                    messages=messages,
                    temperature=self._temperature,
                    max_tokens=self._max_tokens,
                    response_format={"type": "json_object"}
                )
                logger.info(datetime.now(timezone.utc))
                logger.info("API Response:", extra={"response": response})

                try:
                    response_content = response.choices[0].message.content
                    response_json = json.loads(response_content)
                    message = response_json.get("query", "")
                    logger.info(message)
                    return message
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse JSON response: {response}")
                    return response.choices[0].message.content,

            except RateLimitError as e:
                logger.warning(f"Rate limit encountered (attempt {attempt}): {str(e)}")

                if attempt == self._max_retries:
                    logger.error("Max retries reached. Raising exception.")
                    raise

                wait_time = await self._exponential_backoff(attempt)
                logger.info(f"Waiting {wait_time:.2f} seconds before retry")
                await asyncio.sleep(wait_time)

            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                raise
