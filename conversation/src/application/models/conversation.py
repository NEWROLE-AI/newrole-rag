from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class Message:
    """
    Represents a message in the conversation.

    Attributes:
        message_id (str): The unique ID of the message.
        content (str): The content of the message.
        role (str): The role of the sender (e.g., "user", "assistant").
        timestamp (datetime): The timestamp of when the message was created.
    """

    message_id: str
    content: str
    role: str
    user_id: str
    timestamp: datetime = datetime.now(timezone.utc)

    def to_dict(self) -> dict:
        """
        Converts the message to a dictionary format for serialization.

        Returns:
            dict: The serialized message as a dictionary.
        """
        return {
            "message_id": self.message_id,
            "user_id": self.user_id,
            "content": self.content,
            "role": self.role,
            "timestamp": self.timestamp.isoformat(),
        }

    def to_dict_ai(self) -> dict:
        """
        Converts the message to a dictionary format suitable for AI service consumption.

        Returns:
            dict: The serialized message for AI service.
        """
        return {
            "role": self.role,
            "content": [{"type": "text", "text": self.content}],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Message:
        """
        Creates a Message object from a dictionary.

        Args:
            data (dict): The data to populate the Message fields.

        Returns:
            Message: The created Message instance.
        """
        return Message(
            message_id=data.get("message_id"),
            content=data.get("content"),
            role=data.get("role"),
            timestamp=datetime.fromisoformat(data.get("timestamp")),
            user_id=data.get("user_id", ""),
        )


@dataclass
class Conversation:
    """
    Represents a conversation between a user and an agent chat bot.

    Attributes:
        conversation_id (str): The unique ID of the conversation.
        agent_chat_bot_id (str): The ID of the associated agent chat bot.
        messages (list): A list of messages exchanged in the conversation.
    """

    conversation_id: str
    agent_chat_bot_id: str
    messages: list[Message] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """
        Converts the conversation to a dictionary format for serialization.

        Returns:
            dict: The serialized conversation as a dictionary.
        """
        return {
            "conversation_id": self.conversation_id,
            "agent_chat_bot_id": self.agent_chat_bot_id,
            "messages": [message.to_dict() for message in self.messages],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Conversation:
        """
        Creates a Conversation object from a dictionary.

        Args:
            data (dict): The data to populate the Conversation fields.

        Returns:
            Conversation: The created Conversation instance.
        """
        return cls(
            conversation_id=data["conversation_id"],
            agent_chat_bot_id=data["agent_chat_bot_id"],
            messages=[
                Message.from_dict(message) for message in data.get("messages", [])
            ],
        )
