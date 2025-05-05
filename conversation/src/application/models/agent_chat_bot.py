from dataclasses import dataclass


@dataclass
class Prompt:
    """
    Represents a prompt used by the agent chat bot.

    Attributes:
        prompt_id (str): The unique ID of the prompt.
        text (str): The content of the prompt.
    """

    prompt_id: str
    text: str


@dataclass
class AgentChatBot:
    """
    Represents an agent chat bot configuration.

    Attributes:
        agent_chat_bot_id (str): The ID of the agent chat bot.
        knowledge_base_id (str): The ID of the associated knowledge base.
        prompt (Prompt): The prompt used by the agent chat bot.
    """

    agent_chat_bot_id: str
    knowledge_base_id: str
    prompt: Prompt
