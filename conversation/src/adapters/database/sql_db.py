from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker


def get_session_maker(database_url: str) -> async_sessionmaker[AsyncSession]:
    """
    Creates an asynchronous session maker for interacting with the database.

    Args:
        database_url (str): The URL of the database.

    Returns:
        async_sessionmaker[AsyncSession]: The session maker for creating sessions.
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
    Creates an asynchronous session from the session maker.

    Args:
        session_maker (async_sessionmaker[AsyncSession]): The session maker.

    Yields:
        AsyncSession: The database session.
    """
    async with session_maker() as session:
        yield session


async def get_custom_session(
    session_maker: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    """
    Creates an asynchronous session from the session maker.

    Args:
        session_maker (async_sessionmaker[AsyncSession]): The session maker.

    Yields:
        AsyncSession: The database session.
    """
    async with session_maker() as session:
        yield session
