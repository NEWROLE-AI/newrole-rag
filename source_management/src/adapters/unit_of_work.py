import json
import os
from dataclasses import asdict
from datetime import datetime, UTC, timezone

import hvac
from aws_lambda_powertools import Logger
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from sqlalchemy import update, select, delete, text
from sqlalchemy.ext.asyncio import AsyncSession
from boto3_type_annotations.dynamodb import Client
from boto3_type_annotations.secretsmanager import Client as SecretsManagerClient

from src.application.exceptions.domain_exception import DomainException
from src.application.exceptions.value_error_exception import (
    CustomValueError,
    ErrorStatus,
)
from src.application.models.knowledge_base import KnowledgeBase
from src.application.models.realtime_resource import RealtimeResource, RealtimeResourceType, RestApi, Database, DbType
from src.application.models.vectorized_resource import Resource, VectorizedResourceType
from src.application.ports.database_manager import DatabaseType
from src.application.ports.unit_of_work import (
    ResourceRepository,
    UnitOfWork,
    KnowledgeBaseRepository,
    SlackChannelRepository,
    DatabaseRepository, RealtimeResourceRepository, RealtimeDatabaseRepository,
)

logger = Logger("sql_unit_of_work")


class DynamoResourceRepository(ResourceRepository):
    """
    DynamoDB repository for managing resource data.
    """

    def __init__(self, dynamo_client: Client, table_name: str) -> None:
        """
        Initializes the DynamoDB resource repository.

        Args:
            dynamo_client: The DynamoDB client.
            knowledge_base_table_name: The name of the knowledge base table.
        """
        self._dynamo_client = dynamo_client
        self._resources = self._dynamo_client.Table(table_name)

    async def add(self, resource: Resource) -> None:
        """
        Adds a new resource to DynamoDB.
        """
        logger.info(f"Adding resource: {resource}")

        try:
            item = resource.to_dict()
            logger.info(f"Adding resource item: {item}")
            self._resources.put_item(Item=item)

            logger.info(f"Resource {resource.resource_id} added successfully")

        except ClientError as e:
            logger.error(f"Error adding resource: {e}")
            raise

    async def get(self, resource_id: str) -> Resource:
        """
        Fetches a resource by its ID from DynamoDB.
        """
        logger.info(f"Fetching resource with ID: {resource_id}")

        result = self._resources.get_item(Key={'resource_id': resource_id})

        if 'Item' in result:
            item = result['Item']
            return Resource.from_dict(item)
        else:
            raise CustomValueError(
                error_status=ErrorStatus.NOT_FOUND,
                message=f"Resource with ID {resource_id} not found"
            )

    async def get_by_knowledge_base_id(self, knowledge_base_id: str) -> list[dict]:
        response = self._resources.query(
            KeyConditionExpression=Key('knowledge_base_id').eq(knowledge_base_id)
        )
        return response.get('Items', [])



class SqlResourceRepository(ResourceRepository):
    """
    SQL repository for managing resource data.

    This class interacts with the database to perform CRUD operations related to resources.
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Initializes the SqlResourceRepository with an AsyncSession.

        Args:
            session (AsyncSession): The SQLAlchemy AsyncSession instance used for database interactions.
        """
        self._session = session

    async def add(self, resource: Resource) -> None:
        """
        Adds a new resource to the database.

        Args:
            resource (Resource): The resource object to add.

        Raises:
            CustomValueError: If the associated knowledge base does not exist.
        """
        logger.info(f"Adding resource: {resource}")
        # Query to fetch knowledge base ID associated with the resource's knowledge_base_id
        get_kb_id_query = text(
            """
                    SELECT id FROM knowledge_bases
                    WHERE knowledge_base_id = :knowledge_base_id
                """
        )
        result = await self._session.execute(
            get_kb_id_query, {"knowledge_base_id": resource.knowledge_base_id}
        )
        row = result.fetchone()
        if not row:
            logger.error(
                f"Knowledge base with ID {resource.knowledge_base_id} not found"
            )
            raise CustomValueError(
                error_status=ErrorStatus.NOT_FOUND,
                message=f"Knowledge base with ID {resource.knowledge_base_id} does not exist",
            )
        knowledge_base_id = row[0]
        # Insert new resource into the database
        insert_resource_query = text(
            """
                    INSERT INTO resources (resource_id, knowledge_base_id, type, extension, google_drive_url, dynamodb_table_name)
                    VALUES (:resource_id, :knowledge_base_id, :type, :extension, :google_drive_url, :dynamodb_table_name)
                """
        )
        await self._session.execute(
            insert_resource_query,
            {
                "resource_id": resource.resource_id,
                "knowledge_base_id": knowledge_base_id,  # Using ID from knowledge_bases table
                "type": resource.type.value,
                "extension": (
                    resource.extra.extension
                    if hasattr(resource.extra, "extension")
                    else None
                ),
                "google_drive_url": (
                    resource.extra.google_drive_url
                    if hasattr(resource.extra, "google_drive_url")
                    else None
                ),
                "dynamodb_table_name": (
                    resource.extra.table_name
                    if hasattr(resource.extra, "table_name")
                    else None
                ),
            },
        )
        logger.info(f"Resource {resource.resource_id} added successfully")

    async def get(self, resource_id: str) -> Resource:
        """
        Fetches a resource by its ID.

        Args:
            resource_id (str): The resource ID to fetch.

        Returns:
            Resource: The fetched resource object.

        Raises:
            CustomValueError: If the resource with the specified ID does not exist.
        """
        logger.info(f"Fetching resource with ID: {resource_id}")
        query = text(
            """
                   SELECT resource_id, knowledge_base_id, type
                   FROM resources
                   WHERE resource_id = :resource_id
               """
        )
        result = await self._session.execute(query, {"resource_id": resource_id})
        row = result.fetchone()
        if row:
            return Resource(
                resource_id=row.resource_id,
                knowledge_base_id=row.knowledge_base_id,
                type=VectorizedResourceType(row.type),
            )
        else:
            raise CustomValueError(
                error_status=ErrorStatus.NOT_FOUND,
                message=f"Resource with ID {resource_id} not found",
            )


class SqlKnowledgeBaseRepository(KnowledgeBaseRepository):
    """
    SQL repository for managing knowledge base data.

    This class interacts with the database to perform CRUD operations related to knowledge bases.
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Initializes the SqlKnowledgeBaseRepository with an AsyncSession.

        Args:
            session (AsyncSession): The SQLAlchemy AsyncSession instance used for database interactions.
        """
        self._session = session

    async def add(self, knowledge_base: KnowledgeBase) -> None:
        """
        Adds a new knowledge base to the database.

        Args:
            knowledge_base (KnowledgeBase): The knowledge base object to add.
        """
        logger.info(f"Adding knowledge base: {knowledge_base}")
        query = text(
            """
                    INSERT INTO knowledge_bases (knowledge_base_id, name)
                    VALUES (:knowledge_base_id, :name)
                """
        )
        await self._session.execute(
            query,
            {
                "knowledge_base_id": knowledge_base.knowledge_base_id,
                "name": knowledge_base.name,
            },
        )

    async def get(self, knowledge_base_id: str) -> KnowledgeBase:
        """
        Fetches a knowledge base by its ID.

        Args:
            knowledge_base_id (str): The knowledge base ID to fetch.

        Returns:
            KnowledgeBase: The fetched knowledge base object.

        Raises:
            CustomValueError: If the knowledge base with the specified ID does not exist.
        """
        logger.info(f"Fetching knowledge base with ID: {knowledge_base_id}")
        query = text(
            """
                    SELECT knowledge_base_id, name
                    FROM knowledge_bases
                    WHERE knowledge_base_id = :knowledge_base_id
                """
        )
        result = await self._session.execute(
            query, {"knowledge_base_id": knowledge_base_id}
        )
        row = result.fetchone()
        if row:
            return KnowledgeBase(
                knowledge_base_id=row.knowledge_base_id,
                name=row.name,
            )
        else:
            raise CustomValueError(
                error_status=ErrorStatus.NOT_FOUND,
                message=f"Knowledge base with ID {knowledge_base_id} not found",
            )


class DynamoSlackChannelRepository(SlackChannelRepository):
    """
    SQL repository for managing resource data.

    This class interacts with the database to perform CRUD operations related to resources.
    """

    def __init__(self, dynamo_client: Client):
        """
        Initializes the DynamoConversationRepository with a DynamoDB client.

        Args:
            dynamo_client (Client): The DynamoDB client used for accessing the service.
        """
        self._dynamo_client = dynamo_client
        env = os.environ.get("ENVIRONMENT")
        self._slack_channels = self._dynamo_client.Table(
            f"slack-channel-info-resources-{env}"
        )

    async def save(self, resource: Resource) -> None:
        """
        Adds a new additional Slack channel resource to the database.

        Args:
            resource (Resource): The resource object to add.

        Raises:
            ClientError: If the associated knowledge base does not exist.
        """
        try:
            self._slack_channels.put_item(
                Item={
                    "resource_id": resource.resource_id,
                    "channel_id": resource.extra.channel_id,
                    "messages": [
                        message.to_dict() for message in resource.extra.messages
                    ],
                }
            )
            logger.info(f"Saved messages for resource {resource.resource_id}")
        except ClientError as e:
            logger.error(f"Failed to save messages: {e}")
            raise


class SecretsManagerDatabaseRepository(DatabaseRepository):
    """Repository for managing database connection parameters in AWS Secrets Manager."""

    def __init__(self, secrets_manager_client: SecretsManagerClient):
        """
        Initialize the repository with AWS Secrets Manager client.

        Args:
            secrets_manager_client (SecretsManagerClient): Boto3 Secrets Manager client
        """
        self._secrets_manager_client = secrets_manager_client
        self._secret_name_prefix = "database_info"

    async def add(self, resource: Resource) -> None:
        """
        Store database connection parameters in AWS Secrets Manager.

        Args:
            resource (Resource): Resource containing database connection parameters

        Raises:
            DomainException: If the resource is invalid or there's an error storing the secret
        """
        if not resource.extra or not hasattr(resource.extra, "connection_params"):
            logger.error("Invalid resource: missing connection parameters")
            raise DomainException("Invalid resource: missing connection parameters")

        secret_name = f"{self._secret_name_prefix}/{resource.knowledge_base_id}/{resource.resource_id}"

        # Create the secret value with connection parameters and metadata
        secret_value = {
            "connection_params": resource.extra.connection_params,
            "query": resource.extra.query,
            "metadata": {
                "resource_id": resource.resource_id,
                "knowledge_base_id": resource.knowledge_base_id,
                "created_at": datetime.now(UTC).isoformat(),
            },
        }

        try:
            # Try to create a new secret
            await self._create_secret(secret_name, secret_value)
            logger.info(
                "Successfully stored database connection parameters",
                extra={
                    "resource_id": resource.resource_id,
                    "knowledge_base_id": resource.knowledge_base_id,
                },
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceExistsException":
                # If secret exists, update it
                await self._update_secret(secret_name, secret_value)
                logger.info(
                    "Successfully updated database connection parameters",
                    extra={
                        "resource_id": resource.resource_id,
                        "knowledge_base_id": resource.knowledge_base_id,
                    },
                )
            else:
                logger.error(
                    "Failed to store database connection parameters",
                    extra={"error": str(e), "resource_id": resource.resource_id},
                )
                raise DomainException(f"Failed to store database connection: {str(e)}")

    async def _create_secret(self, secret_name: str, secret_value: dict) -> None:
        """Helper method to create a new secret."""
        self._secrets_manager_client.create_secret(
            Name=secret_name, SecretString=json.dumps(secret_value)
        )

    async def _update_secret(self, secret_name: str, secret_value: dict) -> None:
        """Helper method to update an existing secret."""
        self._secrets_manager_client.update_secret(
            SecretId=secret_name, SecretString=json.dumps(secret_value)
        )

class VaultManagerDatabaseRepository(DatabaseRepository):
    """Repository for managing database connection parameters in HashiCorp Vault."""

    def __init__(self, client: hvac.Client, ):
        self._client = client
        if not self._client.is_authenticated():
            logger.error("Vault authentication failed")
            raise DomainException("Could not authenticate to Vault")
        self._secret_path_prefix = "secret/data/database_info"

    async def add(self, resource: Resource) -> None:
        """
        Store or update database connection parameters in Vault.

        Args:
            resource (Resource): Resource containing database connection parameters
        Raises:
            DomainException: If the resource is invalid or there's an error storing the secret
        """
        # Валидация входных данных
        if not resource.extra or not hasattr(resource.extra, "connection_params"):
            logger.error("Invalid resource: missing connection parameters")
            raise DomainException("Invalid resource: missing connection parameters")

        path = f"{self._secret_path_prefix}/{resource.knowledge_base_id}/{resource.resource_id}"

        secret_data = {
            "data": {
                "connection_params": resource.extra.connection_params,
                "query": getattr(resource.extra, "query", None),
                "metadata": {
                    "resource_id": resource.resource_id,
                    "knowledge_base_id": resource.knowledge_base_id,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                },
            }
        }

        try:
            read_resp = self._client.secrets.kv.v2.read_secret_version(path=path)

            self._client.secrets.kv.v2.create_or_update_secret(
                path=path,
                secret=secret_data['data']
            )
            logger.info(
                "Successfully updated Vault database connection parameters",
                extra={"path": path}
            )
        except hvac.exceptions.InvalidPath:

            self._client.secrets.kv.v2.create_or_update_secret(
                path=path,
                secret=secret_data['data']
            )
            logger.info(
                "Successfully stored new Vault database connection",
                extra={"path": path}
            )
        except Exception as e:
            logger.error(
                "Failed to store database connection in Vault",
                extra={"error": str(e), "path": path}
            )
            raise DomainException(f"Failed to store database connection: {str(e)}")


class SqlRealtimeResourceRepository(RealtimeResourceRepository):

    def __init__(self, session: AsyncSession) -> None:
        """
        Initializes the SqlKnowledgeBaseRepository with an AsyncSession.

        Args:
            session (AsyncSession): The SQLAlchemy AsyncSession instance used for database interactions.
        """
        self._session = session

    async def add(self, realtime_resource: RealtimeResource) -> None:
        query = text(
            """
            INSERT INTO realtime_resources (resource_id, knowledge_base_id, type, rest_api_url)
            VALUES (:resource_id, :knowledge_base_id, :type, :rest_api_url, :database_secret_path)
            """
        )
        await self._session.execute(
            query,
            {
                "resource_id": realtime_resource.resource_id,
                "knowledge_base_id": realtime_resource.knowledge_base_id,
                "type": realtime_resource.type,
                "rest_api_url": realtime_resource.extra.url,
                "database_secret_path": realtime_resource.extra.secret_path
            },
        )

    async def get_by_id(self, resource_id: str) -> RealtimeResource:
        query = text(
            """
            SELECT * FROM realtime_resources WHERE resource_id = :resource_id
            """
        )
        cursor = await self._session.execute(query, {"resource_id": resource_id})
        result = cursor.fetchone()
        if len(result) == 0:
            raise ValueError(f"Realtime resource with ID {resource_id} not found")

        if result.rest_api_url:
            extra = RestApi(result.rest_api_url)
        else:
            extra = None

        return RealtimeResource(
            resource_id=result.resource_id,
            knowledge_base_id=result.knowledge_base_id,
            type=RealtimeResourceType(result.type),
            extra=extra
        )

class DynamodbRealtimeResourceRepository(RealtimeResourceRepository):


    def __init__(self, dynamo_client: Client, table_name: str) -> None:
        self._dynamo_client = dynamo_client
        self._realtime_resources = self._dynamo_client.Table(table_name)

    async def add(self, resource: RealtimeResource) -> None:
        """
        Adds a new realtime resource to DynamoDB.
        """
        logger.info(f"Adding resource: {resource}")

        try:
            item = {
                'resource_id': resource.resource_id,
                'knowledge_base_id': resource.knowledge_base_id,
                'type': resource.type.value,
            }
            if resource.type == RealtimeResourceType.REST_API:
                item["url"] = resource.extra.url
            elif resource.type == RealtimeResourceType.DATABASE:
                item["connection_params"] = resource.extra.connection_params
                item["db_type"] = resource.extra.db_type.value

            self._realtime_resources.put_item(Item=item)

            logger.info(f"Resource {resource.resource_id} added successfully")

        except ClientError as e:
            logger.error(f"Error adding resource: {e}")
            raise

    async def get_by_id(self, resource_id: str) -> RealtimeResource:
        """
        Fetches a realtime resource by its ID from DynamoDB.
        """
        logger.info(f"Fetching resource with ID: {resource_id}")

        result = self._realtime_resources.get_item(Key={'resource_id': resource_id})

        if 'Item' in result:
            item = result['Item']
            realtime_resource = RealtimeResource(
                resource_id=item['resource_id'],
                knowledge_base_id=item['knowledge_base_id'],
                type=RealtimeResourceType(item['type']),
            )

            if 'url' in item:
                extra = RestApi(url=item['url'])
            elif 'connection_params' in item:
                extra = Database(
                    connection_params=item['connection_params'],
                    db_type=DbType(item['db_type'])
                )
            else:
                extra = None

            realtime_resource.extra = extra
            return realtime_resource

        else:
            raise CustomValueError(
                error_status=ErrorStatus.NOT_FOUND,
                message=f"Resource with ID {resource_id} not found"
            )


class SecretRealtimeDatabaseRepository(RealtimeDatabaseRepository):
    """Repository for managing database connection parameters in AWS Secrets Manager."""

    def __init__(self, secrets_manager_client: SecretsManagerClient):
        """
        Initialize the repository with AWS Secrets Manager client.

        Args:
            secrets_manager_client (SecretsManagerClient): Boto3 Secrets Manager client
        """
        self._secrets_manager_client = secrets_manager_client
        self._secret_name_prefix = "database_info"

    async def add(self, resource: RealtimeResource) -> RealtimeResource:
        """
        Store database connection parameters in AWS Secrets Manager.

        Args:
            resource (Resource): Resource containing database connection parameters

        Raises:
            DomainException: If the resource is invalid or there's an error storing the secret
        """
        if not resource.extra or not hasattr(resource.extra, "connection_params"):
            logger.error("Invalid resource: missing connection parameters")
            raise ValueError("Invalid resource: missing connection parameters")

        secret_name = f"{self._secret_name_prefix}/{resource.knowledge_base_id}/{resource.resource_id}"

        # Create the secret value with connection parameters and metadata
        secret_value = {
            "connection_params": resource.extra.connection_params,
            "metadata": {
                "resource_id": resource.resource_id,
                "knowledge_base_id": resource.knowledge_base_id,
                "created_at": datetime.now(UTC).isoformat(),
            },
        }
        try:
            # Try to create a new secret
            await self._create_secret(secret_name, secret_value)
            logger.info(
                "Successfully stored database connection parameters",
                extra={
                    "resource_id": resource.resource_id,
                    "knowledge_base_id": resource.knowledge_base_id,
                },
            )
            resource.extra.secret_path = secret_name
            return resource
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceExistsException":
                # If secret exists, update it
                await self._update_secret(secret_name, secret_value)
                logger.info(
                    "Successfully updated database connection parameters",
                    extra={
                        "resource_id": resource.resource_id,
                        "knowledge_base_id": resource.knowledge_base_id,
                    },
                )
            else:
                logger.error(
                    "Failed to store database connection parameters",
                    extra={"error": str(e), "resource_id": resource.resource_id},
                )
                raise DomainException(f"Failed to store database connection: {str(e)}")

    async def get_connection_params_by_id(self, resource_id: str, knowledge_base_id: str) -> dict[str, str]:
        return json.loads(self._secrets_manager_client.get_secret_value(SecretId=f"{self._secret_name_prefix}/{knowledge_base_id}/{resource_id}")['SecretString'])

    async def _create_secret(self, secret_name: str, secret_value: dict) -> None:
        """Helper method to create a new secret."""
        self._secrets_manager_client.create_secret(
            Name=secret_name, SecretString=json.dumps(secret_value)
        )

    async def _update_secret(self, secret_name: str, secret_value: dict) -> None:
        """Helper method to update an existing secret."""
        self._secrets_manager_client.update_secret(
            SecretId=secret_name, SecretString=json.dumps(secret_value)
        )


class UnitOfWorkImpl(UnitOfWork):
    """
    A Unit of Work pattern implementation for managing database transactions.

    This class coordinates the work of multiple repositories within a single transaction.
    It handles commits and ensures repositories are properly initialized and cleaned up.
    """

    resources: DynamoResourceRepository
    knowledge_bases: SqlKnowledgeBaseRepository
    slack_channels: DynamoSlackChannelRepository
    databases: SecretsManagerDatabaseRepository | VaultManagerDatabaseRepository
    realtime_resources: DynamodbRealtimeResourceRepository
    realtime_databases: SecretRealtimeDatabaseRepository

    def __init__(
        self,
        session: AsyncSession,
        dynamo_client: Client,
        secrets_manager_client,
        dynamodb_table_name: str,
    ) -> None:
        """
        Initializes the SqlUnitOfWork with a given SQLAlchemy AsyncSession.

        Args:
            session (AsyncSession): The SQLAlchemy AsyncSession instance.
            dynamo_client (Client): The DynamoDB client for conversation management.
            secrets_manager_client (SecretsManagerClient): The aws secrets manager client for connection params management
        """
        self.session = session
        self._dynamo_client = dynamo_client
        self._secrets_manager_client = secrets_manager_client
        self._dynamodb_table_name = dynamodb_table_name

    async def commit(self) -> None:
        """
        Commits the current transaction to the database.
        """
        logger.info("Committing transaction")
        await self.session.commit()

    async def __aenter__(self):
        """
        Begins a new unit of work, initializing repositories for the current session.

        Returns:
            SqlUnitOfWork: The current unit of work instance.
        """
        logger.info("Starting new unit of work")
        self.resources = DynamoResourceRepository(self._dynamo_client, self._dynamodb_table_name)
        self.knowledge_bases = SqlKnowledgeBaseRepository(self.session)
        self.slack_channels = DynamoSlackChannelRepository(self._dynamo_client)
        # self.databases = SecretsManagerDatabaseRepository(self._secrets_manager_client)
        self.databases = VaultManagerDatabaseRepository(self._secrets_manager_client)
        self.realtime_resources = DynamodbRealtimeResourceRepository(self._dynamo_client, self._dynamodb_table_name)
        self.realtime_databases = SecretRealtimeDatabaseRepository(self._secrets_manager_client)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Handles cleanup when the unit of work is finished.

        If an exception occurs during the unit of work, it logs the error.
        """
        if exc_type:
            logger.error(f"Error occurred: {exc_val}")
        self.resources = None  # type: ignore
        self.knowledge_bases = None  # type: ignore
        self.slack_channels = None  # type: ignore
        self.databases = None  # type: ignore
        self.realtime_resources = None  # type: ignore
