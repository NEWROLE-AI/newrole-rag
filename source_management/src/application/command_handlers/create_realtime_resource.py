import uuid

from aws_lambda_powertools import Logger

from src.application.command_handlers.base import BaseCommandHandler
from src.application.commands.create_realtime_resource import CreateRealtimeResourceCommand
from src.application.exceptions.domain_exception import DomainException
from src.application.models.realtime_resource import RealtimeResourceType, RealtimeResource, Database, RestApi
from src.application.ports.database_manager import DatabaseManager
from src.application.ports.storage_manager import StorageManager
from src.application.ports.unit_of_work import UnitOfWork

logger = Logger(service="create_realtime_resource_handler")


class CreateRealtimeResourceCommandHandler(BaseCommandHandler):
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
        database_manager: DatabaseManager,
    ):
        self._unit_of_work = unit_of_work
        self._handlers = {
            RealtimeResourceType.DATABASE: self._database_handler,
            RealtimeResourceType.REST_API: self._rest_api_handler,
        }
        self._database_manager = database_manager


    async def __call__(self, command: CreateRealtimeResourceCommand):
        """
        Processes a CreateResourceCommand.

        The method routes the command to the appropriate handler based on the resource type.

        Args:
            command(CreateRealtimeResourceCommand): A CreateResourceCommand containing resource details.

        Returns:
            dict: A dictionary with the result of resource creation, including a presigned URL.

        Raises:
            DomainException: If the resource type is not supported or the resource cannot be created.
        """
        handler = self._handlers.get(command.realtime_resource_type)
        if not handler:
            logger.info(
                "There is no resource handler of this type",
                extra={"type": command.realtime_resource_type},
            )
            raise DomainException("It is not possible to process this type of resource")
        result = await handler(command)
        return result


    async def _database_handler(self, command: CreateRealtimeResourceCommand):
        """
        Handles the creation of a database resource.

        This method retrieves the associated knowledge base and stores the resource in the repository.

        Args:
            command(CreateRealtimeResourceCommand): A CreateResourceCommand containing details of the database.

        Returns:
            dict: A dictionary with the `resource_id` for the resource.

        Raises:
            CustomValueError: If the knowledge base does not exist or other errors occur.
        """
        logger.info("Start create database resource")
        await self._database_manager.check_database_connection(
            command.connection_params
        )

        async with self._unit_of_work as uow:
            knowledge_base = await uow.knowledge_bases.get(command.knowledge_base_id)

            resource = RealtimeResource(
                resource_id=str(uuid.uuid4()),
                type=command.realtime_resource_type,
                knowledge_base_id=knowledge_base.knowledge_base_id,
                extra=Database(
                    connection_params=command.connection_params, db_type=command.db_type
                ),
            )
            await uow.realtime_resources.add(resource)
            await uow.realtime_databases.add(resource)
            await uow.commit()
        logger.info("Resource created")
        return {"resource_id": resource.resource_id}


    async def _rest_api_handler(self, command: CreateRealtimeResourceCommand):
        logger.info("Start create rest api resource")

        async with self._unit_of_work as uow:
            knowledge_base = await uow.knowledge_bases.get(command.knowledge_base_id)

            resource = RealtimeResource(
                resource_id=str(uuid.uuid4()),
                type=command.realtime_resource_type,
                knowledge_base_id=knowledge_base.knowledge_base_id,
                extra=RestApi(
                    url=command.url
                )
            )

            await uow.realtime_resources.add(resource)
        logger.info("Resource created")
        return {"resource_id": resource.resource_id}