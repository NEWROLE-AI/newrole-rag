from dataclasses import dataclass

from src.application.commands.base import BaseCommand


@dataclass
class CreateConversationCommand(BaseCommand):
    """
    Command model for creating a new conversation.

    Attributes:
        agent_chat_bot_id (str): The ID of the agent chat bot initiating the conversation.
    """

    agent_chat_bot_id: str
