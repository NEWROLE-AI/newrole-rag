import uuid

from aws_lambda_powertools import Logger

from src.application.command_handlers.base import BaseCommandHandler
from src.application.commands.create_agent_chat_bot import CreateAgentChatBotCommand
from src.application.exceptions.domain_exception import DomainException
from src.application.models.agent_chat_bot import AgentChatBot
from src.application.ports.unit_of_work import UnitOfWork


logger = Logger(service="create_knowledge_base_handler")


class CreateAgentChatBotCommandHandler(BaseCommandHandler):
    """
    Command handler for creating a new agent chat bot.

    This handler processes a `CreateAgentChatBotCommand`, which contains the bot's name,
    prompt ID, and knowledge base ID. It creates a new agent chat bot with a unique ID
    and stores it in the database using the agent chat bot repository.

    Attributes:
        _unit_of_work (UnitOfWork): Handles interactions with the database repositories.
    """

    def __init__(self, unit_of_work: UnitOfWork):
        """
        Initializes the create agent chat bot command handler.

        Args:
            unit_of_work (UnitOfWork): The unit of work for managing database transactions.
        """
        self._unit_of_work = unit_of_work

    async def __call__(self, command: CreateAgentChatBotCommand):
        """
        Handles the create agent chat bot command by creating and storing a new chat bot.

        Args:
            command (CreateAgentChatBotCommand): The command object containing the bot's details.

        Returns:
            dict: The response containing the newly created agent chat bot ID.
        """
        logger.info(
            "Start create agent chat bot",
            extra={"command": command},
        )
        async with self._unit_of_work as uow:
            # Create a new agent chat bot with a unique ID
            agent = AgentChatBot(
                agent_chat_bot_id=str(uuid.uuid4()),
                name=command.name,
                prompt_id=command.prompt_id,
                knowledge_base_id=command.knowledge_base_id,
            )
            logger.info(
                "Create agent chat bot",
                extra={
                    "agent_name": agent.name,
                    "prompt_id": agent.prompt_id,
                    "knowledge_base_id": agent.knowledge_base_id,
                },
            )
            # Store the agent chat bot in the database
            await uow.agent_chat_bots.add(agent)
            await uow.commit()
            logger.info("Agent chat bot created")
        return {"agent_chat_bot_id": agent.agent_chat_bot_id}
