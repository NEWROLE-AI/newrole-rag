from sqlalchemy import Table, Column, Integer, String, ForeignKey, TIMESTAMP
from sqlalchemy.orm import registry

# SQLAlchemy registry for metadata mapping
mapper_registry = registry()


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


knowledge_bases = Table(
    "knowledge_bases",
    mapper_registry.metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("knowledge_base_id", String, nullable=False),
    Column("name", String, nullable=False),
)
