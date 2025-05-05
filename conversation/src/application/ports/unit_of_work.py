from abc import ABC, abstractmethod

from src.application.models.agent_chat_bot import AgentChatBot
from src.application.models.vectorized_knowledge import VectorizedKnowledge
from src.application.models.conversation import Conversation


class VectorizedKnowledgeRepository(ABC):
    """
    Repository for managing vectorized knowledge in the system.

    Methods:
        get: Fetches vectorized knowledge for a specific knowledge base and resource IDs.
        get_knn: Retrieves the k-nearest neighbors for a vectorized query.
    """

    @abstractmethod
    async def get(self, knowledge_base_id: str, resource_ids: list[str]):
        raise NotImplementedError

    @abstractmethod
    async def get_knn(
        self, knowledge_base_id: str, resource_ids: list[str], vectorized_query: list
    ):
        raise NotImplementedError


class AgentChatBotRepository(ABC):
    """
    Repository for managing agent chat bots in the system.

    Methods:
        get: Fetches an agent chat bot by its ID.
    """

    @abstractmethod
    async def get(self, agent_chat_bot_id: str) -> AgentChatBot:
        raise NotImplementedError


class ConversationRepository(ABC):
    """
    Repository for managing conversations in the system.

    Methods:
        get: Fetches a conversation by its ID.
        save: Saves a conversation to the database.
    """

    @abstractmethod
    async def get(self, conversation_id: str) -> Conversation | None:
        raise NotImplementedError

    @abstractmethod
    async def save(self, conversation: Conversation):
        raise NotImplementedError


class BackgroundCheckRepository(ABC):
    """
    Repository for managing background_check in the system.

    Methods:
        save: Saves a background_check to the database.
    """
    @abstractmethod
    async def save(self, user_id: str, background_check: dict):
        raise NotImplementedError


class UnitOfWork(ABC):
    """
    Unit of work for managing transactions across multiple repositories.

    Attributes:
        vectorized_knowledge: Repository for vectorized knowledge.
        agent_chat_bots: Repository for agent chat bots.
        conversations: Repository for conversations.

    Methods:
        __aenter__: Begins the transaction.
        __aexit__: Ends the transaction.
        commit: Commits the transaction.
    """

    vectorized_knowledge: VectorizedKnowledgeRepository
    agent_chat_bots: AgentChatBotRepository
    conversations: ConversationRepository
    background_checks: BackgroundCheckRepository

    @abstractmethod
    async def __aenter__(self) -> "UnitOfWork":
        raise NotImplementedError

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        raise NotImplementedError

    @abstractmethod
    async def commit(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def execute(self, query: str) -> list[dict]:
        raise NotImplementedError
