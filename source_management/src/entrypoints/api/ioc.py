import json
import traceback

import boto3
import httplib2
from boto3 import client as boto3_client
from aws_lambda_powertools import Logger
from aws_secretsmanager_caching import SecretCache, SecretCacheConfig
from dependency_injector import providers, containers
from google.oauth2 import service_account
from google_auth_httplib2 import AuthorizedHttp
from googleapiclient.discovery import build as google_client

from src.adapters.database.db import get_session_maker, get_session
from src.adapters.database_manager import DatabaseManagerImpl
from src.adapters.dynamodb_client import DynamoDbClientImpl
from src.adapters.google_drive_api_client import ApiGoogleDriveClient
from src.adapters.query_service import QueryService
from src.adapters.s3_storage_manager import S3StorageManager
from src.adapters.unit_of_work import UnitOfWorkImpl
from src.application.command_handlers.create_knowledge_base import (
    CreateKnowledgeBaseCommandHandler,
)
from src.application.command_handlers.create_resource import (
    CreateResourceCommandHandler,
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
    secret_name = "dev/ai-custom-bot/source-management"
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
        - AWS services configuration (S3, Secrets Manager, DynamoDB)
        - Database connection and session management
        - Storage management
        - Command handlers
        - Query services
    """

    logger.info("Initializing Container")
    # AWS and database client setup
    secrets_manager_client = boto3.client("secretsmanager", region_name="eu-north-1")
    cache_config = SecretCacheConfig()
    secrets_cache = SecretCache(config=cache_config, client=secrets_manager_client)
    secrets = get_secret(secrets_cache)

    # SQL client configuration
    db_session_maker = providers.Resource(
        get_session_maker,
        database_url=secrets.get("database_url"),
    )
    db_session_factory = providers.Resource(
        get_session,
        session_maker=db_session_maker,
    )

    # Dynamo client configuration
    dynamo_client = providers.Singleton(
        boto3.resource, service_name="dynamodb", region_name="eu-north-1"
    )

    # Application components
    s3_client = providers.Singleton(
        boto3_client, service_name="s3", region_name="eu-north-1"
    )

    secrets_client = providers.Singleton(
        boto3_client, service_name="secretsmanager", region_name="eu-north-1"
    )

    # Google Drive client configuration
    google_credentials = service_account.Credentials.from_service_account_info(
                json.loads((secrets.get("google_drive_credentials"))),
                scopes=['https://www.googleapis.com/auth/drive.readonly']
    )

    google_drive_client = providers.Singleton(
        google_client,
        serviceName="drive",
        version="v3",
        http=AuthorizedHttp(
            google_credentials,
            http=httplib2.Http(timeout=10)
        )
    )

    dynamodb_client = providers.Singleton(
        DynamoDbClientImpl,
        dynamodb_client=dynamo_client
    )

    google_drive_api_client = providers.Singleton(
        ApiGoogleDriveClient,
        google_drive_client=google_drive_client
    )

    storage_manager = providers.Factory(
        S3StorageManager,
        client=s3_client,
        bucket_name=secrets.get("s3_bucket_name"),
    )

    data_base_manager = providers.Factory(
        DatabaseManagerImpl
    )

    unit_of_work = providers.Factory(
        UnitOfWorkImpl,
        session=db_session_factory,
        dynamo_client=dynamo_client,
        secrets_manager_client=secrets_client,
        dynamodb_table_name=secrets.get("dynamodb_table_name"),
    )

    # Command handlers configuration
    create_knowledge_base_handler = providers.Factory(
        CreateKnowledgeBaseCommandHandler,
        unit_of_work=unit_of_work,
    )

    create_resource_handler = providers.Factory(
        CreateResourceCommandHandler,
        unit_of_work=unit_of_work,
        storage_manager=storage_manager,
        google_drive_api_client=google_drive_api_client,
        data_base_manager=data_base_manager,
        dynamodb_client=dynamodb_client,
    )

    query_service = providers.Factory(
        QueryService,
        sql_session=db_session_factory,
        dynamo_client=dynamo_client,
        secrets_manager_client=secrets_client,
    )

    logger.info("Initialized Container complete")
