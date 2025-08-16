from abc import ABC, abstractmethod

from src.application.models.realtime_resource import RealtimeResource
from src.application.models.vectorized_resource import Resource
from src.application.models.knowledge_base import KnowledgeBase


class KnowledgeBaseRepository(ABC):
    @abstractmethod
    async def add(self, knowledge_base: KnowledgeBase) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get(self, knowledge_base_id: str) -> KnowledgeBase:
        raise NotImplementedError


class ResourceRepository(ABC):
    @abstractmethod
    async def add(self, resource: Resource) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_knowledge_base_id(self, knowledge_base_id: str) -> list[dict]:
        raise NotImplementedError


class SlackChannelRepository(ABC):
    @abstractmethod
    async def save(self, resource: Resource) -> None:
        raise NotImplementedError


class DatabaseRepository(ABC):
    @abstractmethod
    async def add(self, resource: Resource) -> None:
        raise NotImplementedError



class RealtimeResourceRepository(ABC):

    @abstractmethod
    async def add(self, resource: RealtimeResource) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, resource_id: str) -> RealtimeResource:
        raise NotImplementedError


class RealtimeDatabaseRepository(ABC):

    @abstractmethod
    async def add(self, resource: RealtimeResource) -> None:
        raise NotImplementedError

    async def get_connection_params_by_id(self, resource_id: str, knowledge_base_id: str) -> dict[str, str]:
        raise NotImplementedError


class UnitOfWork(ABC):
    """
    Unit of Work pattern for managing database transactions.

    This pattern ensures that changes to the database are committed or rolled back as a unit.
    """

    knowledge_bases: KnowledgeBaseRepository
    resources: ResourceRepository
    slack_channels: SlackChannelRepository
    databases: DatabaseRepository
    realtime_resources: RealtimeResourceRepository
    realtime_databases: RealtimeDatabaseRepository

    @abstractmethod
    async def commit(self) -> None:
        """Commits the transaction."""
        raise NotImplementedError

    @abstractmethod
    async def __aenter__(self) -> "UnitOfWork":
        """Async entry method for the UnitOfWork context manager."""
        raise NotImplementedError

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async exit method for the UnitOfWork context manager."""
        raise NotImplementedError
