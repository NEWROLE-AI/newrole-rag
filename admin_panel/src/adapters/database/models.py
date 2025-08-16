from sqlalchemy import Table, Column, Integer, String, ForeignKey, TIMESTAMP
from sqlalchemy.orm import registry
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from sqlalchemy import DateTime, Float

mapper_registry = registry()


resources = Table(
    "prompts",
    mapper_registry.metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("prompt_id", String, nullable=False),
    Column("text", String, nullable=False),
)


knowledge_bases = Table(
    "agent_chat_bots",
    mapper_registry.metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("agent_chat_bot_id", String, nullable=False),
    Column("name", String, nullable=False),
    Column("prompt_id", Integer, ForeignKey("prompts.id"), nullable=True),
    Column("knowledge_base_id", String, nullable=True),
)

# Assuming Base and other necessary imports are available
# For demonstration purposes, defining a minimal Base and User class
# In a real application, these would be properly defined elsewhere.

from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    prompts = relationship("Prompt", back_populates="user")
    agent_chat_bots = relationship("AgentChatBot", back_populates="user")


class Prompt(Base):
    __tablename__ = "prompts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    text = Column(String, nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="prompts")


class AgentChatBot(Base):
    __tablename__ = "agent_chat_bots"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    model = Column(String, nullable=False)
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=1000)
    system_prompt = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="agent_chat_bots")