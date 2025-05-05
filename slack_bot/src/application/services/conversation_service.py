from aws_lambda_powertools import Logger

from src.application.ports.api_client import ConversationApiClient


logger = Logger(service="ConversationService")


class ConversationService:
    def __init__(self, api_client: ConversationApiClient):
        self.api_client = api_client

    def process_message(self, channel_id: str, message: str, user_id: str) -> str:
        logger.info("Processing message", extra={"channel_id": channel_id, "text": message, "user_id": user_id})
        response = self.api_client.send_message(channel_id, message, user_id)
        logger.info("Received response from API client", extra={"response": response})
        return response["message"]
