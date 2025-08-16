from contextlib import asynccontextmanager
from typing import AsyncGenerator
import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, create_engine, MetaData
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import relationship, declarative_base, sessionmaker


Base = declarative_base()
metadata = MetaData()

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

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversations = relationship("Conversation", back_populates="user")

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="conversations")

import os

# Database connection for conversation service (using the modified Base and MetaData)
DATABASE_URL_CONVERSATION = os.getenv("DATABASE_URL", "sqlite:///conversation.db")
engine_conversation = create_engine(DATABASE_URL_CONVERSATION)
SessionLocal_conversation = sessionmaker(autocommit=False, autoflush=False, bind=engine_conversation)

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    content = Column(String, nullable=False)
    role = Column(String, nullable=False)  # 'user' or 'assistant'
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

# Update Conversation model to include messages relationship
Conversation.messages = relationship("Message", back_populates="conversation")