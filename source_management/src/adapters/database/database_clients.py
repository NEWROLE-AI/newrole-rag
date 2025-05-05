import aiomysql
import asyncpg
import aioodbc
from aws_lambda_powertools import Logger

from src.application.ports.database_client import DatabaseClient


logger = Logger("database_clients")


class PostgreSQLClient(DatabaseClient):
    """PostgreSQL database client implementation."""

    def __init__(self, connection_params: dict[str, str]):
        self.connection_params = connection_params
        self.conn: asyncpg.Connection | None = None

    async def connect(self) -> None:
        try:
            self.conn = await asyncpg.connect(**self.connection_params)
            logger.info("Successfully connected to PostgreSQL database")
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL database: {str(e)}")
            raise

    async def close(self) -> None:
        if self.conn:
            await self.conn.close()
            logger.info("PostgreSQL connection closed")

class MySQLClient(DatabaseClient):
    """MySQL database client implementation."""

    def __init__(self, connection_params: dict[str, str]):
        self.connection_params = connection_params
        self.pool = None

    async def connect(self) -> None:
        try:
            self.pool = await aiomysql.create_pool(**self.connection_params)
            logger.info("Successfully connected to MySQL database")
        except Exception as e:
            logger.error(f"Failed to connect to MySQL database: {str(e)}")
            raise

    async def close(self) -> None:
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
            logger.info("MySQL connection closed")

class MsSqlClient(DatabaseClient):
    """MS SQL Server database client implementation."""

    def __init__(self, connection_params: dict[str, str]):
        self.connection_params = connection_params
        self.conn: aioodbc.Connection | None = None

    async def connect(self) -> None:
        # Формируем строку DSN
        dsn = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={self.connection_params.get('host')},{self.connection_params.get('port')};"
            f"DATABASE={self.connection_params.get('database')};"
            f"UID={self.connection_params.get('user')};"
            f"PWD={self.connection_params.get('password')};"
        )
        try:
            self.conn = await aioodbc.connect(dsn=dsn)
            logger.info("Successfully connected to MS SQL Server database")
        except Exception as e:
            logger.error(f"Failed to connect to SQL Server database: {str(e)}")
            raise

    async def close(self) -> None:
        if self.conn:
            await self.conn.close()
            logger.info("MS SQL Server connection closed")
