from sqlalchemy import Table, Column, Integer, String, ForeignKey, TIMESTAMP
from sqlalchemy.orm import registry, relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

# SQLAlchemy registry for metadata mapping
mapper_registry = registry()

Base = declarative_base()

resources = Table(
    "resources",
    mapper_registry.metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("resource_id", String, nullable=False),
    Column(
        "knowledge_base_id",
        Integer,
        ForeignKey("knowledge_bases.id", ondelete="CASCADE"),
        nullable=True,
    ),
    Column("type", String, nullable=False),
    Column("extension", String, nullable=True),
    Column("google_drive_url", String, nullable=True),
    Column("dynamodb_table_name", String, nullable=True),
)


class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=False, unique=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    # Relationships
    knowledge_bases = relationship("KnowledgeBase", back_populates="user")


class KnowledgeBase(Base):
    __tablename__ = "knowledge_bases"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(String)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="knowledge_bases")