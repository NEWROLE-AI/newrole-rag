from abc import ABC, abstractmethod

from src.application.models.prompt import Prompt
from src.application.models.agent_chat_bot import AgentChatBot


class AgentChatBotRepository(ABC):
    """Repository interface for managing agent chat bots."""

    @abstractmethod
    async def add(self, agent_chat_bot: AgentChatBot) -> None:
        """
        Add a new agent chat bot to the repository.

        Args:
            agent_chat_bot: AgentChatBot object to store
        """
        raise NotImplementedError

    @abstractmethod
    async def get(self, agent_chat_bot_id: str) -> AgentChatBot:
        """
        Retrieve an agent chat bot by ID.

        Args:
            agent_chat_bot_id: Unique identifier of the chat bot

        Returns:
            AgentChatBot object containing bot configuration and state
        """
        raise NotImplementedError

    @abstractmethod
    async def update(self, agent_chat_bot_id: str, **kwargs):
        """
        Update an existing agent chat bot's settings.

        Args:
            agent_chat_bot_id: Unique identifier of the chat bot to update
            **kwargs: Settings to update, may include prompt_id and knowledge_base_id
        """
        raise NotImplementedError


class PromptRepository(ABC):
    """Repository interface for managing prompts."""

    @abstractmethod
    async def add(self, prompt: Prompt) -> None:
        """
        Add a new prompt to the repository.

        Args:
            prompt: Prompt object to store
        """
        raise NotImplementedError


class UnitOfWork(ABC):
    """
    Unit of Work interface for managing transactions.

    Implements the Unit of Work pattern to maintain consistency
    across multiple repository operations.

    Attributes:
        agent_chat_bots: Repository for managing chat bot entities
        prompts: Repository for managing prompt entities
    """

    agent_chat_bots: AgentChatBotRepository
    prompts: PromptRepository

    @abstractmethod
    async def commit(self) -> None:
        """Commit all changes made within the transaction."""
        raise NotImplementedError

    @abstractmethod
    async def __aenter__(self) -> "UnitOfWork":
        """Set up the unit of work transaction."""
        raise NotImplementedError

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up the unit of work transaction."""
        raise NotImplementedError
