import asyncio
import json
import os
import traceback

import boto3
import dotenv
from aws_lambda_powertools import Logger
from aws_secretsmanager_caching import SecretCache, SecretCacheConfig
from boto3 import client as boto3_client
from dependency_injector import containers, providers

from src.adapters.fasttext_vectorizer import FastTextVectorizer

logger = Logger(service="VectorizationService")
dotenv.load_dotenv()

if os.getenv("CONTAINER_TYPE") == "aws":

    def get_secret(secrets_cache: SecretCache, env: str) -> dict:
        """
        Retrieves secrets from AWS Secrets Manager.

        Args:
            secrets_cache (SecretCache): AWS Secrets Manager cache instance
            env (str): Environment (dev/prod)

        Returns:
            dict: Dictionary containing secret values

        Raises:
            RuntimeError: If secret retrieval fails
        """
        secret_name = f"{env}/ai-custom-bot/vectorization"
        try:
            logger.info(f"Getting secret {secret_name}")
            secret_value = secrets_cache.get_secret_string(secret_name)
            logger.info(f"Secret retrieved successfully")
            return json.loads(secret_value)
        except Exception as e:
            logger.error(e)
            logger.error(traceback.format_exc())
            logger.error(f"Failed to get secret {secret_name}")
            raise RuntimeError(f"Failed to fetch secret {secret_name}: {str(e)}")


    class AwsContainer(containers.DeclarativeContainer):
        """
        Dependency Injection container for AWS Lambda environment.

        Provides:
            - AWS services configuration (S3, Secrets Manager)
            - FastText vectorizer with S3 model storage
            - Singleton model instance for Lambda reuse
        """

        region = os.environ.get("REGION", "eu-north-1")
        environment = os.environ.get("ENVIRONMENT", "dev")

        logger.info("Initializing AWS Container")

        # AWS Secrets Manager client setup
        secrets_manager_client = providers.Singleton(
            boto3.client,
            service_name="secretsmanager",
            region_name=region,
        )

        cache_config = providers.Object(SecretCacheConfig())

        secrets_cache = providers.Singleton(
            SecretCache,
            config=cache_config,
            client=secrets_manager_client,
        )

        secrets = providers.Factory(
            get_secret,
            secrets_cache=secrets_cache,
            env=environment,
        )

        # S3 client configuration
        s3_client = providers.Singleton(
            boto3_client,
            service_name="s3",
            region_name=region,
        )

        # FastText vectorizer with S3 backend
        fasttext_vectorizer = providers.Singleton(
            FastTextVectorizer,
            client=s3_client,
            bucket_name=secrets.provided.s3_bucket_name_vectorization_model,
            model_s3_key=secrets.provided.model_s3_key.provided.as_("cc.en.300.bin"),
            local_model_path=providers.Object("/tmp/cc.en.300.bin"),
        )

        logger.info("AWS Container initialized")

        _initialized = False
        _lock = asyncio.Lock()

        @classmethod
        async def initialize_app(cls):
            """
            Initializes FastText vectorizer.
            Ensures initialization happens only once (thread-safe).
            """
            async with cls._lock:
                if cls._initialized:
                    logger.info("Application already initialized, skipping")
                    return

                logger.info("Initializing application...")
                try:
                    fasttext_vectorizer_instance = cls.fasttext_vectorizer()

                    # Load model (will download from S3 if needed)
                    fasttext_vectorizer_instance.load_model()

                    logger.info("FastText model loaded successfully")
                    cls._initialized = True
                except Exception as e:
                    logger.error(f"Failed to initialize application: {e}")
                    logger.error(traceback.format_exc())
                    raise


elif os.getenv("CONTAINER_TYPE") == "fastapi":

    def load_secrets():
        """
        Load secrets from Vault (stg/prod) or environment variables (dev).

        Returns:
            dict: Dictionary containing secret values

        Raises:
            ValueError: If environment is not supported
        """
        env = os.getenv("ENVIRONMENT", "dev")

        if env in ["stg", "prod"]:
            import hvac

            client = hvac.Client(
                url=os.getenv("VAULT_ADDR", "http://localhost:8200"),
                token=os.getenv("VAULT_TOKEN"),
            )
            assert client.is_authenticated(), "Vault authentication failed"

            secret_path = os.getenv("SECRET_PATH", "ai-custom-bot/vectorization")
            return client.secrets.kv.read_secret_version(path=secret_path)["data"]["data"]

        elif env == "dev":
            return {
                "base_url_vectorization": os.getenv("BASE_URL_VECTORIZATION"),
                "model_public_url": os.getenv(
                    "MODEL_PUBLIC_URL",
                    "https://dl.fbaipublicfiles.com/fasttext/vectors-crawl/cc.en.300.bin.gz",
                ),
                "local_model_path": os.getenv("LOCAL_MODEL_PATH", "./tmp/cc.en.300.bin"),
            }

        else:
            raise ValueError(f"Unsupported ENVIRONMENT: {env}")


    class FastapiContainer(containers.DeclarativeContainer):
        """
        Dependency Injection container for FastAPI application.

        Provides:
            - Vault secrets management
            - FastText vectorizer with local/public URL model storage
            - Singleton model instance for application reuse
        """

        logger.info("Initializing FastAPI Container")

        # Load secrets from Vault or environment
        secrets = load_secrets()

        # Vault client configuration (for stg/prod)
        secrets_client = providers.Singleton(
            lambda: __import__("hvac").Client(
                url=os.getenv("VAULT_ADDR", "http://localhost:8200"),
                token=os.getenv("VAULT_TOKEN", "root"),
            )
            if os.getenv("ENVIRONMENT") in ["stg", "prod"]
            else None,
        )

        # FastText vectorizer without S3 (uses direct download)
        fasttext_vectorizer = providers.Singleton(
            FastTextVectorizer,
            client=None,  # No S3 in FastAPI mode
            bucket_name=None,
            model_s3_key=None,
            local_model_path=secrets.get("local_model_path", "./tmp/cc.en.300.bin"),
            model_url=secrets.get(
                "model_public_url",
                "https://dl.fbaipublicfiles.com/fasttext/vectors-crawl/cc.en.300.bin.gz",
            ),
        )

        logger.info("FastAPI Container initialized")

        _initialized = False
        _lock = asyncio.Lock()
        _vectorizer_instance = None
        @classmethod
        async def initialize_app(cls):
            """
            Initializes FastText vectorizer.
            Ensures initialization happens only once (thread-safe).
            """
            async with cls._lock:
                if cls._initialized:
                    logger.info("Application already initialized, skipping")
                    return

                logger.info("Initializing application...")
                try:
                    # Получить singleton экземпляр ОДИН раз
                    if cls._vectorizer_instance is None:
                        cls._vectorizer_instance = cls.fasttext_vectorizer()

                    # Загрузить модель только если еще не загружена
                    if not hasattr(cls._vectorizer_instance, 'model') or cls._vectorizer_instance.model is None:
                        cls._vectorizer_instance.load_model()
                        logger.info("FastText model loaded successfully")
                    else:
                        logger.info("FastText model already loaded, skipping")

                    cls._initialized = True
                except Exception as e:
                    logger.error(f"Failed to initialize application: {e}")
                    logger.error(traceback.format_exc())
                    raise

        @classmethod
        async def shutdown_app(cls):
            """
            Cleanup resources on application shutdown.
            """
            logger.info("Shutting down application...")
            # Add cleanup logic if needed (e.g., close connections)
            cls._initialized = False
            logger.info("Application shutdown complete")
