import asyncio
import json
import traceback

import boto3
from aws_lambda_powertools import Logger
from dependency_injector import containers, providers
from boto3 import client as boto3_client
from aws_secretsmanager_caching import SecretCache, SecretCacheConfig

from src.adapters.fasttext_vectorizer import FastTextVectorizer


logger = Logger(service="VectorizationService")


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
    secret_name = "dev/ai-custom-bot/vectorization"
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
    """

    logger.info("Initializing Container")
    # Configuration and wiring setup
    wiring_config = containers.WiringConfiguration(modules=[".fastapi_handlers"])
    config = providers.Configuration()

    logger.info("Initializing Service")
    # AWS and database client setup
    secrets_manager_client = boto3.client("secretsmanager", region_name="eu-north-1")
    cache_config = SecretCacheConfig()
    secrets_cache = SecretCache(config=cache_config, client=secrets_manager_client)
    secrets = get_secret(secrets_cache)

    s3_client = providers.Singleton(
        boto3_client, service_name="s3", region_name="eu-north-1"
    )

    fasttext_vectorizer = providers.Singleton(
        FastTextVectorizer,
        client=s3_client,
        bucket_name=secrets.get("s3_bucket_name_vectorization_model"),
        model_s3_key="cc.en.300.bin",
    )

    logger.info("Initialized Container complete")
    _initialized = False

    @classmethod
    async def initialize_app(cls):
        """
        Initializes application components including index manager and FastText vectorizer.
        Ensures initialization happens only once.
        """
        if cls._initialized:
            return

        logger.info("Initializing application...")
        fasttext_vectorizer_instance = cls.fasttext_vectorizer()
        fasttext_vectorizer_instance.load_model(
            cls.secrets.get("s3_vectorization_model")
        )
        logger.info("Application initialized successfully")
        cls._initialized = True
