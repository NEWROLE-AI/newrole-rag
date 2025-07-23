import json
import os
import traceback

import aiohttp
import boto3
import httplib2
import hvac
from boto3 import client as boto3_client
from aws_lambda_powertools import Logger
from aws_secretsmanager_caching import SecretCache, SecretCacheConfig
from dependency_injector import providers, containers
from google.oauth2 import service_account
from google_auth_httplib2 import AuthorizedHttp
from googleapiclient.discovery import build as google_client
from opensearchpy import AsyncOpenSearch

from src.adapters.database.db import get_session_maker, get_session
from src.adapters.database_manager import DatabaseManagerImpl
from src.adapters.dynamodb_client import DynamoDbClientImpl
from src.adapters.google_drive_api_client import ApiGoogleDriveClient
from src.adapters.opensearch_service import OpensearchVectorizedKnowledgeService
from src.adapters.query_service import QueryService
from src.adapters.realtime_api_service import IoHttpRealtimeApiService
from src.adapters.realtime_database_service import PostgresRealtimeDatabaseService, MySqlRealtimeDatabaseService
from src.adapters.s3_storage_manager import S3StorageManager
from src.adapters.unit_of_work import UnitOfWorkImpl
from src.adapters.vectorized_service import HttpVectorizedService
from src.application.command_handlers.create_knowledge_base import (
    CreateKnowledgeBaseCommandHandler,
)
from src.application.command_handlers.create_realtime_resource import CreateRealtimeResourceCommandHandler
from src.application.command_handlers.create_vectorized_resource import (
    CreateVectorizedResourceCommandHandler,
)
from src.application.command_handlers.get_realtime_data import GetRealtimeDataCommandHandler
from src.application.command_handlers.get_vectorized_data import GetVectorizedDataCommandHandler
from src.application.models.realtime_resource import DbType

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
    secret_name = f"{env}/ai-custom-bot/source-management"
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


class AwsContainer(containers.DeclarativeContainer):
    """
    Dependency Injection container that configures and provides all service dependencies.

    Provides:
        - AWS services configuration (S3, Secrets Manager, DynamoDB)
        - Database connection and session management
        - Storage management
        - Command handlers
        - Query services
    """

    # region = os.environ.get("REGION")
    # environment = os.environ.get("ENVIRONMENT")
    # logger.info("Initializing Container")
    # # AWS and database client setup
    # secrets_manager_client = providers.Singleton(
    #     boto3.client,
    #     service_name="secretsmanager",
    #     region_name=region,
    # )
    #
    # cache_config = providers.Object(SecretCacheConfig())
    #
    # secrets_cache = providers.Singleton(
    #     SecretCache,
    #     config=cache_config,
    #     client=secrets_manager_client,
    # )
    #
    # secrets = providers.Factory(
    #     get_secret,
    #     secrets_cache=secrets_cache,
    #     env=environment,
    # )
    #
    # # SQL client configuration
    # db_session_maker = providers.Resource(
    #     get_session_maker,
    #     database_url=secrets.get("database_url"),
    # )
    # db_session_factory = providers.Resource(
    #     get_session,
    #     session_maker=db_session_maker,
    # )
    #
    # # Dynamo client configuration
    # dynamo_client = providers.Singleton(
    #     boto3.resource, service_name="dynamodb", region_name=region
    # )
    #
    # # Applicatio   n components
    # s3_client = providers.Singleton(boto3_client, service_name="s3", region_name=region)
    #
    # secrets_client = providers.Singleton(
    #     boto3_client, service_name="secretsmanager", region_name=region
    # )
    #
    # # Google Drive client configuration
    # google_credentials = service_account.Credentials.from_service_account_info(
    #     json.loads((secrets.get("google_drive_credentials"))),
    #     scopes=["https://www.googleapis.com/auth/drive.readonly"],
    # )
    #
    # google_drive_client = providers.Singleton(
    #     google_client,
    #     serviceName="drive",
    #     version="v3",
    #     http=AuthorizedHttp(google_credentials, http=httplib2.Http(timeout=10)),
    # )
    #
    # dynamodb_client = providers.Singleton(
    #     DynamoDbClientImpl, dynamodb_client=dynamo_client
    # )
    #
    # google_drive_api_client = providers.Singleton(
    #     ApiGoogleDriveClient, google_drive_client=google_drive_client
    # )
    #
    # storage_manager = providers.Singleton(
    #     S3StorageManager,
    #     client=s3_client,
    #     bucket_name=secrets.get("s3_bucket_name"),
    # )
    #
    # database_manager = providers.Factory(DatabaseManagerImpl)
    #
    # unit_of_work = providers.Singleton(
    #     UnitOfWorkImpl,
    #     session=db_session_factory,
    #     dynamo_client=dynamo_client,
    #     secrets_manager_client=secrets_client,
    #     dynamodb_table_name=secrets.get("dynamodb_table_name"),
    # )
    #
    # # Command handlers configuration
    # create_knowledge_base_handler = providers.Singleton(
    #     CreateKnowledgeBaseCommandHandler,
    #     unit_of_work=unit_of_work,
    # )
    #
    # create_resource_handler = providers.Singleton(
    #     CreateVectorizedResourceCommandHandler,
    #     unit_of_work=unit_of_work,
    #     storage_manager=storage_manager,
    #     google_drive_api_client=google_drive_api_client,
    #     data_base_manager=database_manager,
    #     dynamodb_client=dynamodb_client,
    # )
    #
    # query_service = providers.Singleton(
    #     QueryService,
    #     sql_session=db_session_factory,
    #     dynamo_client=dynamo_client,
    #     secrets_manager_client=secrets_client,
    # )
    #
    # http_session = providers.Singleton(
    #     aiohttp.ClientSession
    # )
    #
    # api_service = providers.Singleton(
    #     IoHttpRealtimeApiService,
    #     session=http_session
    # )
    #
    # create_realtime_resource_handler = providers.Singleton(
    #     CreateRealtimeResourceCommandHandler,
    #     unit_of_work=unit_of_work,
    #     database_manager=database_manager,
    # )
    #
    # http_session = providers.Singleton(
    #     aiohttp.ClientSession,
    # )
    #
    # vectorize_service = providers.Singleton(
    #     HttpVectorizedService,
    #     secrets.get("base_url"),
    #     session=http_session,
    # )
    #
    # elastic_search_client = providers.Singleton(
    #     AsyncOpenSearch,
    #     hosts=[secrets.get("opensearch_host")],
    #     http_auth=(
    #         secrets.get("opensearch_username"),
    #         secrets.get("opensearch_password"),
    #     ),
    #     verify_certs=True,
    #     timeout=60,
    #     max_retries=10,
    #     retry_on_timeout=True,
    # )
    #
    # vectorized_knowledge_service = providers.Singleton(
    #     OpensearchVectorizedKnowledgeService,
    #     client=elastic_search_client,
    #     knn_parameter=25,
    # )
    #
    # get_vectorized_data_service = providers.Singleton(
    #     GetVectorizedDataCommandHandler,
    #     unit_of_work=unit_of_work,
    #     vectorize_service=vectorize_service,
    #     vectorized_knowledge_service=vectorized_knowledge_service,
    # )
    # postgresql_handler = providers.Singleton(
    #     PostgresRealtimeDatabaseService
    # )
    #
    # mysql_handler = providers.Singleton(
    #         MySqlRealtimeDatabaseService
    # )
    #
    # db_handlers = providers.Dict({
    #     DbType.POSTGRESQL: postgresql_handler,
    #     DbType.MYSQL: mysql_handler,
    # })
    #
    # get_realtime_data_service = providers.Singleton(
    #     GetRealtimeDataCommandHandler,
    #     unit_of_work=unit_of_work,
    #     api_service=api_service,
    #     db_handlers=db_handlers,
    #     database_manager=database_manager,
    # )
    #
    # logger.info("Initialized Container complete")


class FastapiContainer(containers.DeclarativeContainer):
    region = os.environ.get("REGION")

    #Secrets
    client = hvac.Client(
        url=os.getenv('VAULT_ADDR', 'http://localhost:8200'),
        token=os.getenv('VAULT_TOKEN')
    )

    assert client.is_authenticated()

    secrets = client.secrets.kv.read_secret_version(path=os.getenv('SECRET_PATH'))['data']['data']

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
        boto3.resource, service_name="dynamodb", region_name=region
    )
    # Application components
    # s3_client = providers.Singleton(boto3_client, service_name="s3", region_name=region)

    secrets_client = providers.Singleton(
        hvac.Client,
        url=os.getenv('VAULT_ADDR', 'http://localhost:8200'),
        token=os.getenv('VAULT_TOKEN')
    )

    # Google Drive client configuration
    google_credentials = service_account.Credentials.from_service_account_info(
        json.loads((secrets.get("google_drive_credentials"))),
        scopes=["https://www.googleapis.com/auth/drive.readonly"],
    )

    google_drive_client = providers.Singleton(
        google_client,
        serviceName="drive",
        version="v3",
        http=AuthorizedHttp(
            # google_credentials,
            None,
            http=httplib2.Http(timeout=10)),
    )

    dynamodb_client = providers.Singleton(
        DynamoDbClientImpl, dynamodb_client=dynamo_client
    )

    google_drive_api_client = providers.Singleton(
        ApiGoogleDriveClient, google_drive_client=google_drive_client
    )

    # storage_manager = providers.Singleton(
    #     S3StorageManager,
    #     client=s3_client,
    #     bucket_name=secrets.get("s3_bucket_name"),
    # )

    data_base_manager = providers.Factory(DatabaseManagerImpl)

    secrets_manager_client = providers.Singleton(
        hvac.Client,
        url=os.getenv('VAULT_ADDR', 'http://localhost:8200'),
        token=os.getenv('VAULT_TOKEN')
    )

    unit_of_work = providers.Singleton(
        UnitOfWorkImpl,
        session=db_session_factory,
        dynamo_client=dynamo_client,
        secrets_manager_client=secrets_client,
        dynamodb_table_name=secrets.get("dynamodb_table_name"),
    )

    # Command handlers configuration
    create_knowledge_base_handler = providers.Singleton(
        CreateKnowledgeBaseCommandHandler,
        unit_of_work=unit_of_work,
    )

    create_resource_handler = providers.Singleton(
        CreateVectorizedResourceCommandHandler,
        unit_of_work=unit_of_work,
        # storage_manager=storage_manager,
        google_drive_api_client=google_drive_api_client,
        data_base_manager=data_base_manager,
        dynamodb_client=dynamodb_client,
    )

    query_service = providers.Singleton(
        QueryService,
        sql_session=db_session_factory,
        dynamo_client=dynamo_client,
        secrets_manager_client=secrets_client,
    )

    logger.info("Initialized Container complete")