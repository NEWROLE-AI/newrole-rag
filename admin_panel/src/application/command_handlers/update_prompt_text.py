from aws_lambda_powertools import Logger

from src.application.command_handlers.base import BaseCommandHandler
from src.application.commands.update_prompt_text import UpdatePromptTextCommand
from src.application.ports.unit_of_work import UnitOfWork

logger = Logger(service="update_prompt_text_handler")


class UpdatePromptTextCommandHandler(BaseCommandHandler):
    """
        Command handler for updating the text of an existing prompt.

        This handler processes an `UpdatePromptTextCommand`, which contains the
        prompt's ID and the new text. It updates the existing prompt in the database
        using the prompt repository.

        Attributes:
            _unit_of_work (UnitOfWork): Handles interactions with the database repositories.
        """

    def __init__(self, unit_of_work: UnitOfWork):
        """
        Initializes the update prompt text command handler.

        Args:
            unit_of_work (UnitOfWork): The unit of work for managing database transactions.
        """
        self._unit_of_work = unit_of_work

    async def __call__(self, command: UpdatePromptTextCommand):
        """
        Handles the update prompt text command by updating an existing prompt's text.

        Args:
            command (UpdatePromptTextCommand): The command object containing
                the prompt's ID and new text.

        Returns:
            dict: The response containing the updated prompt ID.
        """
        logger.info(
            "Start updating prompt text",
            extra={"command": command},
        )
        async with self._unit_of_work as uow:
            logger.info(
                "Updating prompt text",
                extra={
                    "prompt_id": command.prompt_id,
                },
            )
            # Update the prompt text in the database
            await uow.prompts.update(
                prompt_id=command.prompt_id,
                text=command.text,
            )
            await uow.commit()
            logger.info("Prompt text updated")
        return {"prompt_id": command.prompt_id}