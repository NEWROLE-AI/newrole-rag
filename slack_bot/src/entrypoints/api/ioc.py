import json
import os
import traceback

from fastapi import FastAPI
from requests import Session
import boto3
from aws_lambda_powertools import Logger
from aws_secretsmanager_caching import SecretCache, SecretCacheConfig
from dependency_injector import containers, providers
from slack_bolt import App

from src.adapters.file_processor import FileProcessorImpl
from src.application.services.conversation_service import ConversationService
from src.application.services.channel_service import ChannelService
from src.adapters.http_api_client import (
    HttpConversationApiClient,
    HttpResourceManagerApiClient,
)
from src.application.handlers.message_handlers import MessageHandler
from src.application.handlers.channel_handlers import ChannelHandler


logger = Logger(service="ioc")


def get_secret(secrets_cache: SecretCache, env: str) -> dict:
    """
    Retrieves secrets from AWS Secrets Manager.

    Args:
        secrets_cache (SecretCache): AWS Secrets Manager cache instance
        env (str): Environment(dev/prod)

    Returns:
        dict: Dictionary containing secret values

    Raises:
        RuntimeError: If secret retrieval fails
    """
    secret_name = f"{env}/ai-custom-bot/slack-bot"
    try:
        logger.info(f"Getting secret {secret_name}")
        secret_value = secrets_cache.get_secret_string(secret_name)
        logger.info(f"Secret value {secret_value}")
        return json.loads(secret_value)
    except Exception as e:
        logger.info(e)
        logger.info(traceback.format_exc())
        logger.info(f"Failed to get secret {secret_name}")
        raise RuntimeError(f"Failed to fetch secret {secret_name}: {str(e)}")


class Container(containers.DeclarativeContainer):
    """
    Dependency Injection container that configures and provides all service dependencies.

    Provides:
        - AWS services configuration (Secrets Manager)
        - Slack bot
        - Command handlers
    """

    region = os.environ.get("REGION")
    environment = os.environ.get("ENVIRONMENT")
    logger.info("Initializing Container")
    # AWS and database client setup
    secrets_manager_client = boto3.client("secretsmanager", region_name=region)
    cache_config = SecretCacheConfig()
    secrets_cache = SecretCache(config=cache_config, client=secrets_manager_client)
    secrets = get_secret(secrets_cache, environment)

    http_session = providers.Singleton(
        Session,
    )

    # Core dependencies
    conversation_api_client = providers.Singleton(
        HttpConversationApiClient,
        conversation_url=secrets.get("conversation_url"),
    )
    resource_manager_api_client = providers.Singleton(
        HttpResourceManagerApiClient,
        source_management_url=secrets.get("resource_manager_url"),
    )

    file_processor = providers.Singleton(
        FileProcessorImpl, token=secrets.get("BOT_TOKEN")
    )

    # Services
    conversation_service = providers.Singleton(
        ConversationService, api_client=conversation_api_client
    )

    channel_service = providers.Singleton(
        ChannelService, api_client=resource_manager_api_client
    )

    dynamo_client = providers.Singleton(
        boto3.resource, service_name="dynamodb", region_name=region
    )

    # Handlers
    message_handler = providers.Singleton(
        MessageHandler,
        conversation_service=conversation_service,
        file_processor=file_processor,
    )
    channel_handler = providers.Singleton(
        ChannelHandler, channel_service=channel_service
    )

    # Slack App
    slack_app = providers.Singleton(
        App,
        token=secrets.get("BOT_TOKEN"),
        signing_secret=secrets.get("SIGNING_SECRET"),
    )
