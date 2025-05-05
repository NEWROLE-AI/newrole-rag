from urllib.parse import urlparse

import sqlparse
from aws_lambda_powertools import Logger

from src.adapters.database.database_clients import (
    PostgreSQLClient,
    MySQLClient,
    MsSqlClient,
)
from src.application.exceptions.value_error_exception import (
    CustomValueError,
    ErrorStatus,
)
from src.application.ports.database_client import DatabaseClient
from src.application.ports.database_manager import DatabaseManager, DatabaseType


logger = Logger(service="database_manager")


class DatabaseManagerImpl(DatabaseManager):
    """
    A service class to manage operations with database resources.

    This class uses DatabaseClient to interact with the database and is intended to be used
    in the context of working with resources related to the knowledge base.
    """

    async def check_query(self, query: str):
        """
        Validation of a database query.
        If a query is invalid, raise CustomValueError.
        For example, it has a delete statement.
        Args:
            query (str): query to be validated.

        Raises:
            CustomValueError: If query is invalid.
        """
        logger.info("Checking database query...")
        parsed = sqlparse.parse(query)
        if not parsed or not all(
            [statement.get_type() == "SELECT" for statement in parsed]
        ):
            raise CustomValueError(
                error_status=ErrorStatus.BAD_REQUEST,
                message="All queries must be a SELECT statement",
            )
        logger.info("Successfully checked database query")

    async def check_database_connection(self, connection_params: dict[str, str]):
        """
        Validation of ta database connection. If not connected, raise CustomValueError.

        Args:
            connection_params (dict[str, str]): connection parameters.

        Raises:
            CustomValueError: If cant connect to a database.
        """

        logger.info("Checking database connection...")
        try:
            client = await self.create_client(connection_params)
            await client.connect()
            logger.info("Successfully connected to PostgreSQL database")
            await client.close()
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL database: {str(e)}")
            raise CustomValueError(
                error_status=ErrorStatus.BAD_REQUEST,
                message="Connection to database resource failed",
            )
        logger.info("Successfully checked database connection")

    def detect_database_type(self, connection_params: dict[str, str]) -> DatabaseType:
        """Detect database type from connection parameters."""

        if database_driver := connection_params.get("database_driver", ""):
            if database_driver == "POSTGRESQL":
                return DatabaseType.POSTGRESQL
            elif database_driver == "MYSQL":
                return DatabaseType.MYSQL
            elif database_driver == "MSSQL":
                return DatabaseType.MSSQL

        # Check for URL/DSN
        if "dsn" in connection_params or "url" in connection_params:
            url = connection_params.get("dsn") or connection_params.get("url")
            parsed = urlparse(url)
            if parsed.scheme in ("postgresql", "postgres"):
                return DatabaseType.POSTGRESQL
            elif parsed.scheme in ("mysql", "mariadb"):
                return DatabaseType.MYSQL
            elif parsed.scheme in ("mssql", "sqlserver"):
                return DatabaseType.MSSQL

        # Check port number
        port = str(connection_params.get("port", ""))
        if port == "5432":
            return DatabaseType.POSTGRESQL
        elif port == "3306":
            return DatabaseType.MYSQL
        elif port == "1433":
            return DatabaseType.MSSQL

        # Check specific parameters
        if "passwd" in connection_params:
            return DatabaseType.MYSQL
        elif "password" in connection_params:
            return DatabaseType.POSTGRESQL
        elif "PWD" in connection_params:
            return DatabaseType.MSSQL

        raise ValueError("Could not determine database type from connection parameters")

    async def create_client(self, connection_params: dict[str, str]) -> DatabaseClient:
        """Create appropriate database client based on connection parameters."""
        db_type = self.detect_database_type(connection_params)
        logger.info(f"Creating client for database type: {db_type}")
        connection_params.pop("database_driver", None)
        if db_type == DatabaseType.POSTGRESQL:
            return PostgreSQLClient(connection_params)
        elif db_type == DatabaseType.MYSQL:
            return MySQLClient(connection_params)
        elif db_type == DatabaseType.MSSQL:
            return MsSqlClient(connection_params)
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
