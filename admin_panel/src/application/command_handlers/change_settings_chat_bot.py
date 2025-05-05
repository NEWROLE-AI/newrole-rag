from aws_lambda_powertools import Logger

from src.application.command_handlers.base import BaseCommandHandler
from src.application.commands.change_settings_chat_bot import (
    ChangeSettingsAgentChatBotCommand,
)
from src.application.ports.unit_of_work import UnitOfWork

logger = Logger(service="create_knowledge_base_handler")


class ChangeSettingsAgentChatBotCommandHandler(BaseCommandHandler):
    """
    Command handler for changing settings of an existing agent chat bot.

    This handler processes a `ChangeSettingsAgentChatBotCommand`, which contains the
    bot's ID and updated settings (prompt ID and knowledge base ID). It updates the
    existing agent chat bot in the database using the agent chat bot repository.

    Attributes:
        _unit_of_work (UnitOfWork): Handles interactions with the database repositories.
    """

    def __init__(self, unit_of_work: UnitOfWork):
        """
        Initializes the change settings agent chat bot command handler.

        Args:
            unit_of_work (UnitOfWork): The unit of work for managing database transactions.
        """
        self._unit_of_work = unit_of_work

    async def __call__(self, command: ChangeSettingsAgentChatBotCommand):
        """
        Handles the change settings command by updating an existing chat bot's settings.

        Args:
            command (ChangeSettingsAgentChatBotCommand): The command object containing
                the bot's ID and updated settings.

        Returns:
            dict: The response containing the updated agent chat bot ID.
        """
        logger.info(
            "Start create agent chat bot",
            extra={"command": command},
        )
        async with self._unit_of_work as uow:
            logger.info(
                "update chat bot",
                extra={
                    "prompt_id": command.prompt_id,
                    "knowledge_base_id": command.knowledge_base_id,
                },
            )
            # Update the agent chat bot settings in the database
            await uow.agent_chat_bots.update(
                agent_chat_bot_id=command.agent_chat_bot_id,
                prompt_id=command.prompt_id,
                knowledge_base_id=command.knowledge_base_id,
            )
            await uow.commit()
            logger.info("Agent chat bot updated")
        return {"agent_chat_bot_id": command.agent_chat_bot_id}
