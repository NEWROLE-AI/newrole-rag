from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker


def get_session_maker(database_url: str) -> async_sessionmaker[AsyncSession]:
    """
    Creates an AsyncSession maker for connecting to the database.

    Args:
        database_url (str): The database connection URL.

    Returns:
        async_sessionmaker: A session maker that can create AsyncSession instances.
    """
    engine = create_async_engine(database_url, pool_size=10, max_overflow=20)
    session_maker = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    return session_maker


async def get_session(
    session_maker: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    """
    Provides an AsyncSession generator for use in database transactions.

    Args:
        session_maker (async_sessionmaker): The session maker used to create AsyncSession instances.

    Yields:
        AsyncSession: A new AsyncSession instance for interacting with the database.
    """
    async with session_maker() as session:
        yield session
