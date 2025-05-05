from aws_lambda_powertools import Logger

from src.application.ports.api_client import ResourceManagerApiClient


logger = Logger(service="ChannelService")


class ChannelService:
    def __init__(self, api_client: ResourceManagerApiClient):
        self.api_client = api_client

    def store_channel_history(self, channel_id: str, messages: list[dict]) -> None:
        logger.info("Adding channel history to resource manager", extra={"channel_id": channel_id})
        self.api_client.add_resource(channel_id, messages)
        logger.info("Channel history added successfully", extra={"channel_id": channel_id})
