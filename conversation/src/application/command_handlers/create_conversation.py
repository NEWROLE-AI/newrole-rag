import uuid

from aws_lambda_powertools import Logger

from src.application.command_handlers.base import BaseCommandHandler
from src.application.commands.create_conversation import CreateConversationCommand
from src.application.models.conversation import Conversation
from src.application.ports.unit_of_work import UnitOfWork


logger = Logger("create_conversation_handler")


class CreateConversationCommandHandler(BaseCommandHandler):
    """
    Command handler for creating a new conversation.

    This handler processes a `CreateConversationCommand`, which contains the agent chat bot ID,
    and creates a new conversation in the system.

    Attributes:
        _unit_of_work (UnitOfWork): Handles database transactions related to conversations.
    """

    def __init__(self, unit_of_work: UnitOfWork):
        """
        Initializes the create conversation command handler with dependencies.

        Args:
            unit_of_work (UnitOfWork): The unit of work for managing database interactions.
        """
        self._unit_of_work = unit_of_work

    async def __call__(self, command: CreateConversationCommand):
        """
        Creates a new conversation by generating a new conversation ID and saving it to the database.

        Args:
            command (CreateConversationCommand): The command containing the agent chat bot ID.

        Returns:
            dict: The response containing the conversation ID.
        """
        logger.info(
            "Start create conversation",
            extra={"command": command},
        )
        async with self._unit_of_work as uow:
            # Create a new conversation object
            conversation = Conversation(
                conversation_id=str(uuid.uuid4()),
                agent_chat_bot_id=command.agent_chat_bot_id,
            )
            logger.info(
                "Create conversation",
                extra={
                    "agent_chat_bot_id": conversation.agent_chat_bot_id,
                    "conversation_id": conversation.conversation_id,
                },
            )

            # Save the conversation to the database
            await uow.conversations.save(conversation)
            logger.info("Agent chat bot created")

        # Return the newly created conversation's ID
        return {"conversation_id": conversation.conversation_id}
