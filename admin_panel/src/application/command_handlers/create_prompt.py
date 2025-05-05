import uuid

from aws_lambda_powertools import Logger

from src.application.command_handlers.base import BaseCommandHandler
from src.application.commands.create_prompt import CreatePromptCommand
from src.application.exceptions.domain_exception import DomainException
from src.application.models.prompt import Prompt
from src.application.ports.unit_of_work import UnitOfWork


logger = Logger(service="create_prompt_handler")


class CreatePromptCommandHandler(BaseCommandHandler):
    """
    Command handler for creating a new prompt.

    This handler processes a `CreatePromptCommand`, which contains the prompt text.
    It creates a new prompt with a unique ID and stores it in the database using
    the prompt repository.

    Attributes:
        _unit_of_work (UnitOfWork): Handles interactions with the database repositories.
    """

    def __init__(self, unit_of_work: UnitOfWork):
        """
        Initializes the create prompt command handler.

        Args:
            unit_of_work (UnitOfWork): The unit of work for managing database transactions.
        """
        self._unit_of_work = unit_of_work

    async def __call__(self, command: CreatePromptCommand):
        """
        Handles the create prompt command by creating and storing a new prompt.

        Args:
            command (CreatePromptCommand): The command object containing the prompt text.

        Returns:
            dict: The response containing the newly created prompt ID.
        """
        logger.info(
            "Start create prompt",
            extra={"command": command},
        )
        async with self._unit_of_work as uow:
            # Create a new prompt with a unique ID
            prompt = Prompt(prompt_id=str(uuid.uuid4()), text=command.text)
            logger.info(
                "Create prompt",
                extra={
                    "prompt_id": prompt.prompt_id,
                },
            )
            # Store the prompt in the database
            await uow.prompts.add(prompt)
            await uow.commit()
            logger.info("Prompt created")
        return {"prompt_id": prompt.prompt_id}
