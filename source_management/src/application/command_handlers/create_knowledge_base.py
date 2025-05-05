import uuid

from aws_lambda_powertools import Logger

from src.application.command_handlers.base import BaseCommandHandler
from src.application.commands.create_knowledge_base import CreateKnowledgeBaseCommand
from src.application.exceptions.domain_exception import DomainException
from src.application.models.knowledge_base import KnowledgeBase
from src.application.ports.unit_of_work import UnitOfWork


# Logger instance from aws_lambda_powertools to log events.
logger = Logger(service="create_knowledge_base_handler")


class CreateKnowledgeBaseCommandHandler(BaseCommandHandler):
    """
    Command handler for creating a new Knowledge Base.

    This handler processes commands to create a new knowledge base in the system.
    It uses the UnitOfWork pattern for managing database transactions.

    Attributes:
        _unit_of_work (UnitOfWork): The unit of work interface for managing data transactions.
    """

    def __init__(self, unit_of_work: UnitOfWork):
        """
        Initializes the command handler with a UnitOfWork instance.

        Args:
            unit_of_work: A UnitOfWork instance for managing transactional work.
        """
        self._unit_of_work = unit_of_work

    async def __call__(self, command: CreateKnowledgeBaseCommand):
        """
        Handles the creation of a new Knowledge Base.

        The method generates a new KnowledgeBase instance, stores it in the repository,
        and commits the changes.

        Args:
            command(CreateKnowledgeBaseCommand): A CreateKnowledgeBaseCommand containing the name of the knowledge base.

        Returns:
            dict: A dictionary with the `knowledge_base_id` of the created knowledge base.

        Raises:
            DomainException: If an error occurs during the creation of the knowledge base.
        """
        logger.info(
            "Start create knowledge base",
            extra={"knowledge_base_name": command.knowledge_base_name},
        )
        async with self._unit_of_work as uow:
            knowledge_base = KnowledgeBase(
                knowledge_base_id=str(uuid.uuid4()), name=command.knowledge_base_name
            )
            logger.info(
                "Create knowledge base",
                extra={
                    "knowledge_base_name": knowledge_base.name,
                    "knowledge_base_id": knowledge_base.knowledge_base_id,
                },
            )
            await uow.knowledge_bases.add(knowledge_base)
            await uow.commit()
            logger.info("Knowledge created")
        return {"knowledge_base_id": knowledge_base.knowledge_base_id}
