import json
import traceback

import aiohttp
import boto3
from anthropic import Anthropic
from aws_lambda_powertools import Logger
from aws_secretsmanager_caching import SecretCache, SecretCacheConfig
from dependency_injector import providers
from dependency_injector.containers import DeclarativeContainer
from opensearchpy import AsyncOpenSearch

from src.adapters.claude_ai_service import ClaudeAIService
from src.adapters.database.sql_db import get_session_maker, get_session
from src.adapters.database.unit_of_work import UnitOfWorkImpl
from src.adapters.http_api_client import (
    HttpSourceManagementApiClient,
    HttpVectorizerApiClient,
)
from src.application.command_handlers.conversation import ConversationCommandHandler

from src.application.command_handlers.create_conversation import (
    CreateConversationCommandHandler,
)

logger = Logger(service="ioc")


def get_secret(secrets_cache: SecretCache) -> dict:
    """
    Retrieves secrets from AWS Secrets Manager.

    Args:
        secrets_cache (SecretCache): AWS Secrets Manager cache instance

    Returns:
        dict: Dictionary containing secret values

    Raises:
        RuntimeError: If secret retrieval fails
    """
    secret_name = "dev/ai-custom-bot/conversation"
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


class Container(DeclarativeContainer):
    """
    Dependency Injection container that configures and provides all service dependencies.

    Provides:
        - AWS services configuration (Secrets Manager, dynamo)
        - Database connection and session management(sql, dynamo, opensearch)
        - Command handlers
    """

    logger.info("Initializing Container")
    # AWS and database client setup
    secrets_manager_client = boto3.client("secretsmanager", region_name="eu-north-1")
    cache_config = SecretCacheConfig()
    secrets_cache = SecretCache(config=cache_config, client=secrets_manager_client)
    secrets = get_secret(secrets_cache)

    # Opensearch client configuration
    elastic_search_client = providers.Singleton(
        AsyncOpenSearch,
        hosts=[secrets.get("opensearch_host")],
        http_auth=(
            secrets.get("opensearch_username"),
            secrets.get("opensearch_password"),
        ),
        verify_certs=True,
        timeout=60,
        max_retries=10,
        retry_on_timeout=True,
    )

    # Application components
    anthropic_client = providers.Factory(
        Anthropic, api_key=secrets.get("claude_api_key")
    )

    ai_service = providers.Factory(
        ClaudeAIService,
        client=anthropic_client,
        temperature=secrets.get("claude_temperature", 0),
        max_tokens=secrets.get("claude_max_tokens", 1000),
        system_prompt=secrets.get("claude_system_prompt", ""),
    )

    http_session = providers.Singleton(
        aiohttp.ClientSession,
    )
    source_management_api_client = providers.Factory(
        HttpSourceManagementApiClient,
        session=http_session,
        source_management_url=secrets.get("source_management_url"),
    )

    vectorizer_api_client = providers.Factory(
        HttpVectorizerApiClient,
        session=http_session,
        vectorize_service_url=secrets.get("vectorize_service_url"),
    )

    # Dynamo client configuration
    dynamo_client = providers.Singleton(
        boto3.resource, service_name="dynamodb", region_name="eu-north-1"
    )

    # SQL client configuration
    db_session_maker = providers.Resource(
        get_session_maker,
        database_url=secrets.get("database_url"),
    )

    db_session_factory = providers.Resource(
        get_session,
        session_maker=db_session_maker,
    )

    unit_of_work = providers.Factory(
        UnitOfWorkImpl,
        session=db_session_factory,
        opensearch_client=elastic_search_client,
        dynamo_client=dynamo_client,
        knn_parameter=secrets.get("knn_parameter"),
    )

    # Command handlers configuration
    create_conversation_handler = providers.Factory(
        CreateConversationCommandHandler,
        unit_of_work=unit_of_work,
    )

    conversation_handler = providers.Factory(
        ConversationCommandHandler,
        unit_of_work=unit_of_work,
        source_management_api_client=source_management_api_client,
        ai_service=ai_service,
        vectorizer_api_client=vectorizer_api_client,
    )
