from dataclasses import dataclass

from src.application.commands.base import BaseCommand


@dataclass
class ConversationCommand(BaseCommand):
    """
    Command model for processing a conversation.

    Attributes:
        message (str): The message sent by the user.
        conversation_id (str): The ID of the conversation to continue.
    """

    message: str
    user_id: str
    conversation_id: str
