import random
import time
from typing import Any

import requests
from aws_lambda_powertools import Logger
from requests import RequestException, Session, HTTPError

from src.application.ports.api_client import (
    ConversationApiClient,
    ResourceManagerApiClient,
)


logger = Logger("http_api_client")


class HttpConversationApiClient(ConversationApiClient):
    def __init__(self, conversation_url: str):
        self._base_url = conversation_url
        self._max_retries = 3
        self._initial_backoff = 0.5
        self._max_backoff = 60.0

        # Default retry status codes if not specified
        self._retry_on_status_codes = [
            408,  # Request Timeout
            429,  # Too Many Requests
            500,  # Internal Server Error
            502,  # Bad Gateway
            503,  # Service Unavailable
            504,  # Gateway Timeout
        ]

    def _calculate_backoff(self, attempt: int) -> float:
        """
        Calculate exponential backoff time with jitter.

        Args:
            attempt (int): Current retry attempt number.

        Returns:
            float: Wait time in seconds.
        """
        # Exponential backoff calculation
        backoff = min(self._max_backoff, self._initial_backoff * (2 ** (attempt - 1)))

        # Add jitter to prevent synchronized retries
        jitter = backoff * random.uniform(0.5, 1.5)
        return jitter

    def _base_send_message(
        self, url: str, conversation_id: str, message: str, user_id: str
    ) -> dict[str, Any]:
        """
        Send a message with retry mechanism.

        Args:
            conversation_id (str): ID of the conversation
            message (str): Message to send
            user_id (str): ID of the user

        Returns:
            Dict[str, Any]: Response from the API
        """
        data = {
            "conversation_id": conversation_id,
            "message": message,
            "user_id": user_id,
        }

        for attempt in range(1, self._max_retries + 1):
            try:
                logger.info(
                    f"Sending message (Attempt {attempt})",
                    extra={"text": message, "conversation_id": conversation_id, "url": url},
                )

                response = requests.post(url, json=data, timeout=30)

                # Check if status code is in retry list
                if response.status_code in self._retry_on_status_codes:
                    raise HTTPError(
                        f"{response.status_code} Server Error", response=response
                    )

                # Successful response
                if response.status_code == 200:
                    response_message = response.json()
                    logger.info(
                        "HttpConversationApiClient: Successfully sent message",
                        extra={"conversation_id": conversation_id, "attempt": attempt},
                    )
                    return response_message

                # Raise for other non-200 status codes
                response.raise_for_status()

            except (RequestException, HTTPError) as e:
                logger.warning(
                    f"Error sending message (Attempt {attempt}): {str(e)}",
                    extra={
                        "conversation_id": conversation_id,
                        "error_type": type(e).__name__,
                    },
                )

                # If it's the last attempt, raise the exception
                if attempt == self._max_retries:
                    logger.error(
                        "Max retries reached. Raising final exception.",
                        extra={"conversation_id": conversation_id, "error": str(e)},
                    )
                    raise

                # Calculate backoff time
                backoff_time = self._calculate_backoff(attempt)
                logger.info(
                    f"Waiting {backoff_time:.2f} seconds before retry",
                    extra={"attempt": attempt, "backoff_time": backoff_time},
                )

                # Wait before next retry
                time.sleep(backoff_time)

        # This should never be reached due to the raise in the retry loop
        raise RuntimeError("Unexpected error in send_message")

    def send_message(
        self, conversation_id: str, message: str, user_id: str
    ) -> dict[str, Any]:
        """
        Send a message with retry mechanism.

        Args:
            conversation_id (str): ID of the conversation
            message (str): Message to send
            user_id (str): ID of the user

        Returns:
            Dict[str, Any]: Response from the API
        """
        url = self._base_url + "/api/v1/conversations/messages"
        return self._base_send_message(url, conversation_id, message, user_id)

    def send_message_background_check(
        self, conversation_id: str, message: str, user_id: str
    ) -> dict[str, Any]:
        """
        Send a message with retry mechanism.

        Args:
            conversation_id (str): ID of the conversation
            message (str): Message to send
            user_id (str): ID of the user

        Returns:
            Dict[str, Any]: Response from the API
        """
        url = self._base_url + "/api/v1/conversations/messages/background_checks"
        return self._base_send_message(url, conversation_id, message, user_id)


class HttpResourceManagerApiClient(ResourceManagerApiClient):
    def __init__(self, source_management_url: str):
        self._base_url = source_management_url

    def add_resource(self, channel_id: str, messages: list[dict]):
        url = self._base_url + "/api/v1/resources"
        logger.info(
            "HttpResourceManagerApiClient: Conversation",
            extra={"channel_id": channel_id},
        )
        data = {
            "knowledge_base_id": "bdb55006-7508-4173-88f0-78912a596a49",
            "resource_type": "SLACK_CHANNEL",
            "channel_id": channel_id,
            "messages": messages,
        }
        try:
            response = requests.post(url, json=data)
            if response.status_code != 200:
                logger.error(f"Error add resource: {response.status_code}")
                response.raise_for_status()
            response_message = response.json()
            logger.info("HttpResourceManagerApiClient: Successfully add resource")
            return response_message
        except RequestException as e:
            logger.error(f"HTTP RequestException while add resource: {str(e)}")
            raise
