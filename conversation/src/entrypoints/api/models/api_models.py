import datetime

from pydantic import BaseModel


class ConversationRequest(BaseModel):
    """
    Model for the incoming request to fetch a conversation.

    Attributes:
        conversation_id (str): The unique ID of the conversation.
        message (str): The message within the conversation.
    """

    conversation_id: str
    message: str


class ConversationResponse(BaseModel):
    """
    Model for the response containing conversation details.

    Attributes:
        conversation_id (str): The unique ID of the conversation.
        message (str): The message within the conversation.
    """

    conversation_id: str
    message: str


class CreateConversationRequest(BaseModel):
    """
    Model for the incoming request to create a new conversation.

    Attributes:
        agent_chat_bot_id (str): The ID of the agent chat bot initiating the conversation.
    """

    agent_chat_bot_id: str


class CreateConversationResponse(BaseModel):
    """
    Model for the response containing the newly created conversation's details.

    Attributes:
        conversation_id (str): The unique ID of the newly created conversation.
    """

    conversation_id: str


class GetConversationResponse(BaseModel):
    class Conversation(BaseModel):
        conversation_id: str
        agent_chat_bot_id: str

    conversation_list: list[Conversation]


class GetMessagesResponse(BaseModel):
    class Message(BaseModel):
        message_id: str
        role: str
        content: str
        timestamp: datetime.datetime

    messages: list[Message]