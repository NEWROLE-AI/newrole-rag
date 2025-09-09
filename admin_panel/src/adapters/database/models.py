from sqlalchemy import Table, Column, Integer, String, ForeignKey, TIMESTAMP
from sqlalchemy.orm import registry

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
