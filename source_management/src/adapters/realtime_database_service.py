import aiomysql
import asyncpg

from src.application.ports.realtime_database_service import RealtimeDatabaseService


class PostgresRealtimeDatabaseService(RealtimeDatabaseService):

    async def execute_query(self, query: str, connection_params: dict) -> list[dict]:
        conn = await asyncpg.connect(**connection_params)
        await conn.execute(query)
        res = await conn.fetch(query)
        return [dict(row) for row in res]


class MySqlRealtimeDatabaseService(RealtimeDatabaseService):

    async def execute_query(self, query: str, connection_params: dict) -> list[dict]:
        conn = aiomysql.connect(**connection_params)
        await conn.execute(query)
        res = await conn.fetchall()
        return [dict(row) for row in res]