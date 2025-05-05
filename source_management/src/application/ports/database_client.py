from abc import ABC, abstractmethod


class DatabaseClient(ABC):
    """Abstract base class for database clients."""

    @abstractmethod
    async def connect(self) -> None:
        """Establish database connection."""
        raise NotImplementedError

    @abstractmethod
    async def close(self) -> None:
        """Close database connection."""
        raise NotImplementedError
