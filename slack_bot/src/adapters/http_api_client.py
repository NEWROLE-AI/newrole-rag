import requests
from aws_lambda_powertools import Logger
from requests import RequestException, Session

from src.application.ports.api_client import (
    ConversationApiClient,
    ResourceManagerApiClient,
)


logger = Logger("http_api_client")


class HttpConversationApiClient(ConversationApiClient):
    def __init__(self, conversation_url: str):
        self._base_url = conversation_url

    def send_message(self, conversation_id: str, message: str, user_id: str) -> dict:
        url = self._base_url + "/api/v1/conversations/messages"
        logger.info(
            "HttpConversationApiClient: Conversation",
            extra={"text": message, "conversation_id": conversation_id},
        )
        data = {"conversation_id": conversation_id, "message": message, "user_id": user_id}
        try:
            logger.info(f"{url} {data}")
            response = requests.post(url, json=data)
            logger.info(f"{response}")
            if response.status_code != 200:
                logger.error(f"Error conversation: {response.status_code}")
                response.raise_for_status()
            response_message = response.json()
            logger.info(
                "HttpConversationApiClient: Successfully conversation send message"
            )
            return response_message
        except RequestException as e:
            logger.error(
                f"HTTP RequestException while conversation send message: {str(e)}"
            )
            raise


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
            "knowledge_base_id": "46a0db95-d390-486c-ae25-1e248a0235a5",
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
            logger.error(
                f"HTTP RequestException while add resource: {str(e)}"
            )
            raise
