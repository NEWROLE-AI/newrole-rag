from abc import ABC, abstractmethod
from enum import Enum

from src.application.ports.database_client import DatabaseClient


class DatabaseType(str, Enum):
    """Supported database types"""

    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    MSSQL = "mssql"


class DatabaseManager(ABC):
    """
    A service class to manage operations with database resources.

    This class uses DatabaseClient to interact with the database and is intended to be used
    in the context of working with resources related to the knowledge base.
    """

    @abstractmethod
    async def check_query(self, query: str):
        """
        Validation of a database query.
        If a query is invalid, raise CustomValueError.
        For example, it has a delete statement.
        """
        raise NotImplementedError()


    @abstractmethod
    async def check_database_connection(self, connection_params: dict[str, str]):
        """
        Validation of ta database connection. If not connected, raise CustomValueError.
        """
        raise NotImplementedError()

    @abstractmethod
    def detect_database_type(self, connection_params: dict[str, str]) -> DatabaseType:
        """Detect database type from connection parameters."""
        raise NotImplementedError()

    @abstractmethod
    async def create_client(self, connection_params: dict[str, str]) -> DatabaseClient:
        """Create appropriate database client based on connection parameters."""
        raise NotImplementedError()