import json
import os
import traceback

import boto3
from aws_lambda_powertools import Logger
from aws_secretsmanager_caching import SecretCache, SecretCacheConfig
from dependency_injector import providers
from dependency_injector.containers import DeclarativeContainer

from src.adapters.database.db import get_session_maker, get_session
from src.adapters.sql_unit_of_work import SqlUnitOfWork
from src.application.command_handlers.change_settings_chat_bot import (
    ChangeSettingsAgentChatBotCommandHandler,
)
from src.application.command_handlers.create_agent_chat_bot import (
    CreateAgentChatBotCommandHandler,
)
from src.application.command_handlers.create_prompt import CreatePromptCommandHandler
from src.application.command_handlers.update_prompt_text import UpdatePromptTextCommandHandler

logger = Logger(service="ioc")


def get_secret(secrets_cache: SecretCache, env: str) -> dict:
    """
    Retrieves secrets from AWS Secrets Manager.

    Args:
        secrets_cache (SecretCache): AWS Secrets Manager cache instance
        env (str): environment(dev/prod)

    Returns:
        dict: Dictionary containing secret values

    Raises:
        RuntimeError: If secret retrieval fails
    """
    secret_name = f"{env}/ai-custom-bot/admin-panel"
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


class AwsContainer(DeclarativeContainer):
    """
    Dependency Injection container that configures and provides all service dependencies.

    Provides:
        - AWS services configuration (Secrets Manager)
        - Database connection and session management(sql)
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
        SqlUnitOfWork,
        session=db_session_factory,
    )

    # Command handlers configuration
    create_prompt_handler = providers.Factory(
        CreatePromptCommandHandler,
        unit_of_work=unit_of_work,
    )

    create_agent_chat_bot_handler = providers.Factory(
        CreateAgentChatBotCommandHandler,
        unit_of_work=unit_of_work,
    )

    change_settings_agent_chat_bot_handler = providers.Factory(
        ChangeSettingsAgentChatBotCommandHandler,
        unit_of_work=unit_of_work,
    )

    update_prompt_text_handler = providers.Factory(
        UpdatePromptTextCommandHandler,
        unit_of_work=unit_of_work,
    )

class FastapiContainer(DeclarativeContainer):
    """
    Dependency Injection container that configures and provides all service dependencies.

    Provides:
        - Database connection and session management(sql)
        - Command handlers
    """
    # Mock secret
    secrets = {
        "database_url": "",
    }

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
        SqlUnitOfWork,
        session=db_session_factory,
    )

    # Command handlers configuration
    create_prompt_handler = providers.Factory(
        CreatePromptCommandHandler,
        unit_of_work=unit_of_work,
    )

    create_agent_chat_bot_handler = providers.Factory(
        CreateAgentChatBotCommandHandler,
        unit_of_work=unit_of_work,
    )

    change_settings_agent_chat_bot_handler = providers.Factory(
        ChangeSettingsAgentChatBotCommandHandler,
        unit_of_work=unit_of_work,
    )

    update_prompt_text_handler = providers.Factory(
        UpdatePromptTextCommandHandler,
        unit_of_work=unit_of_work,
    )
