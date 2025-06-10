import uuid
from datetime import datetime

from aws_lambda_powertools import Logger

from src.application.command_handlers.base import BaseCommandHandler
from src.application.commands.create_vectorized_resource import CreateVectorizedResourceCommand
from src.application.exceptions.domain_exception import DomainException
from src.application.exceptions.value_error_exception import (
    CustomValueError,
    ErrorStatus,
)
from src.application.models.vectorized_resource import (
    VectorizedResourceType,
    Resource,
    SlackChannel,
    SlackMessage,
    File,
    Database,
    GoogleDrive,
    DynamodbTable,
)
from src.application.ports.database_manager import DatabaseManager
from src.application.ports.dynaodb_client import DynamodbClient
from src.application.ports.google_drive_client import GoogleDriveClient
from src.application.ports.storage_manager import StorageManager
from src.application.ports.unit_of_work import UnitOfWork


logger = Logger(service="create_vectorized_resource_handler")


class CreateVectorizedResourceCommandHandler(BaseCommandHandler):
    """
    Command handler for creating resources.

    This handler processes commands to create different types of resources (e.g., static files).
    It utilizes a UnitOfWork for managing database transactions and interacts with a storage manager
    for generating presigned URLs for resource upload.

    Attributes:
        _unit_of_work (UnitOfWork): The unit of work interface for managing database transactions.
        _storage_manager (StorageManager): Service for managing storage operations like presigned URL generation.
        _handlers (dict): A mapping of resource types to specific handlers.
    """

    def __init__(
        self,
        unit_of_work: UnitOfWork,
        storage_manager: StorageManager,
        google_drive_api_client: GoogleDriveClient,
        data_base_manager: DatabaseManager,
        dynamodb_client: DynamodbClient,
    ):
        """
        Initializes the resource creation handler with dependencies.

        Args:
            unit_of_work: A UnitOfWork instance for managing transactional work.
            storage_manager: A StorageManager instance for handling storage-related tasks.
        """
        self._unit_of_work = unit_of_work
        self._storage_manager = storage_manager
        self._google_drive_api_client = google_drive_api_client
        self._handlers = {
            VectorizedResourceType.STATIC_FILE: self._static_file_handler,
            VectorizedResourceType.SLACK_CHANNEL: self._slack_channel_handler,
            VectorizedResourceType.DATABASE: self._database_handler,
            VectorizedResourceType.GOOGLE_DRIVE: self._google_drive_handler,
            VectorizedResourceType.DYNAMODB_TABLE: self._dynamodb_table_handler,
        }
        self._database_manager = data_base_manager
        self._dynamodb_client = dynamodb_client

    async def __call__(self, command: CreateVectorizedResourceCommand):
        """
        Processes a CreateResourceCommand.

        The method routes the command to the appropriate handler based on the resource type.

        Args:
            command(CreateVectorizedResourceCommand): A CreateResourceCommand containing resource details.

        Returns:
            dict: A dictionary with the result of resource creation, including a presigned URL.

        Raises:
            DomainException: If the resource type is not supported or the resource cannot be created.
        """
        handler = self._handlers.get(command.vectorized_resource_type)
        if not handler:
            logger.info(
                "There is no resource handler of this type",
                extra={"type": command.vectorized_resource_type},
            )
            raise DomainException("It is not possible to process this type of resource")
        result = await handler(command)
        return result

    async def _slack_channel_handler(self, command: CreateVectorizedResourceCommand):
        """
        Handles the creation of a slack_channel resource.

        This method retrieves the associated knowledge base and stores the resource in the repository.

        Args:
            command(CreateVectorizedResourceCommand): A CreateResourceCommand containing details of the slack channel.

        Returns:
            dict: A dictionary with the `resource_id` for the resource.

        Raises:
            CustomValueError: If the knowledge base does not exist or other errors occur.
        """
        logger.info("Start slack channel creation")
        async with self._unit_of_work as uow:
            knowledge_base = await uow.knowledge_bases.get(command.knowledge_base_id)

            messages = [
                SlackMessage(
                    message_id=str(uuid.uuid4()),
                    content=i.get("content"),
                    user_id=i.get("user_id"),
                    timestamp=datetime.fromisoformat(i.get("timestamp")),
                )
                for i in command.messages
            ]
            extra = SlackChannel(channel_id=command.channel_id, messages=messages)
            resource = Resource(
                resource_id=str(uuid.uuid4()),
                type=command.vectorized_resource_type,
                knowledge_base_id=knowledge_base.knowledge_base_id,
                extra=extra,
            )
            await uow.resources.add(resource)
            await uow.slack_channels.save(resource)
            await uow.commit()
            logger.info("Resource created")
            return {"resource_id": resource.resource_id}

    async def _static_file_handler(self, command: CreateVectorizedResourceCommand):
        """
        Handles the creation of a static file resource.

        This method retrieves the associated knowledge base, generates a presigned URL for the resource,
        and stores the resource in the repository.

        Args:
            command(CreateVectorizedResourceCommand): A CreateResourceCommand containing details of the static file.

        Returns:
            dict: A dictionary with the `presigned_url` for the static file resource.

        Raises:
            CustomValueError: If the knowledge base does not exist or other errors occur.
        """
        logger.info("Start create static file resource")
        async with self._unit_of_work as uow:
            knowledge_base = await uow.knowledge_bases.get(command.knowledge_base_id)

            resource = Resource(
                resource_id=str(uuid.uuid4()),
                type=command.vectorized_resource_type,
                knowledge_base_id=knowledge_base.knowledge_base_id,
                extra=File(extension=command.file_type),
            )
            presigned_url = await self._storage_manager.generate_presigned_url(
                knowledge_base_name=knowledge_base.knowledge_base_id,
                resource_name=resource.resource_id,
                file_type=command.file_type,
            )
            logger.info(
                "Generate presigned url", extra={"resource_id": resource.resource_id}
            )
            await uow.resources.add(resource)
            await uow.commit()
            logger.info("Resource created")
            return {"presigned_url": presigned_url, "resource_id": resource.resource_id}

    async def _database_handler(self, command: CreateVectorizedResourceCommand):
        """
        Handles the creation of a database resource.

        This method retrieves the associated knowledge base and stores the resource in the repository.

        Args:
            command(CreateVectorizedResourceCommand): A CreateResourceCommand containing details of the database.

        Returns:
            dict: A dictionary with the `resource_id` for the resource.

        Raises:
            CustomValueError: If the knowledge base does not exist or other errors occur.
        """
        logger.info("Start create database resource")
        await self._database_manager.check_query(command.query)
        await self._database_manager.check_database_connection(
            command.connection_params
        )

        async with self._unit_of_work as uow:
            knowledge_base = await uow.knowledge_bases.get(command.knowledge_base_id)

            resource = Resource(
                resource_id=str(uuid.uuid4()),
                type=command.vectorized_resource_type,
                knowledge_base_id=knowledge_base.knowledge_base_id,
                extra=Database(
                    connection_params=command.connection_params, query=command.query
                ),
            )
            await uow.resources.add(resource)
            await uow.databases.add(resource)
            await uow.commit()
            logger.info("Resource created")
            return {"resource_id": resource.resource_id}

    async def _google_drive_handler(self, command: CreateVectorizedResourceCommand):
        """
        Handles the creation of a Google Drive resource.

        This method retrieves the associated knowledge base and stores the resource in the repository.

        Args:
            command(CreateVectorizedResourceCommand): A CreateResourceCommand containing details of the Google Drive.

        Returns:
            dict: A dictionary with the `resource_id` for the resource.

        Raises:
            CustomValueError: If the knowledge base does not exist or Google Drive url is invalid.
        """
        logger.info("Start create database resource")

        if command.google_drive_url:
            await self._google_drive_api_client.check_google_drive(
                command.google_drive_url
            )

        async with self._unit_of_work as uow:
            knowledge_base = await uow.knowledge_bases.get(command.knowledge_base_id)

            resource = Resource(
                resource_id=str(uuid.uuid4()),
                type=command.vectorized_resource_type,
                knowledge_base_id=knowledge_base.knowledge_base_id,
                extra=GoogleDrive(google_drive_url=command.google_drive_url),
            )
            await uow.resources.add(resource)
            await uow.commit()
            logger.info("Resource created")
            return {"resource_id": resource.resource_id}

    async def _dynamodb_table_handler(self, command: CreateVectorizedResourceCommand):
        """
        Handles the creation of a DynamoDB table resource.
        """
        logger.info("Start create dynamodb table resource")
        self._dynamodb_client.check_connection(command.dynamodb_table_name)
        async with self._unit_of_work as uow:
            knowledge_base = await uow.knowledge_bases.get(command.knowledge_base_id)

            resource = Resource(
                resource_id=str(uuid.uuid4()),
                type=command.vectorized_resource_type,
                knowledge_base_id=knowledge_base.knowledge_base_id,
                extra=DynamodbTable(table_name=command.dynamodb_table_name),
            )
            await uow.resources.add(resource)
            await uow.commit()
            logger.info("Resource created")
            return {"resource_id": resource.resource_id}
