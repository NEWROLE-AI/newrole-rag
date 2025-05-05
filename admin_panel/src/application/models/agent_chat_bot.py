from dataclasses import dataclass


@dataclass
class AgentChatBot:
    """
    Data model representing an agent chat bot.

    Attributes:
        name (str): The name of the chat bot.
        agent_chat_bot_id (str): Unique identifier for the chat bot.
        prompt_id (str): ID of the associated prompt.
        knowledge_base_id (str): ID of the associated knowledge base.
    """

    name: str
    agent_chat_bot_id: str
    prompt_id: str
    knowledge_base_id: str
