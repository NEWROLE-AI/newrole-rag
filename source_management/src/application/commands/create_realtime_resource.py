from dataclasses import dataclass
from typing import Any

from src.application.commands.base import BaseCommand
from src.application.models.realtime_resource import RealtimeResourceType, DbType


@dataclass
class CreateRealtimeResourceCommand(BaseCommand):
    """
    Command for creating a resource (e.g., static file).

    This command contains data about the resource to be created, such as its type,
    the associated knowledge base, and the file type.

    Attributes:
        realtime_resource_type (VectorizedResourceType): The type of the resource (e.g., STATIC_FILE).
        knowledge_base_id (str): The ID of the knowledge base associated with the resource.
        file_type (str | None): The type of file for the resource (optional).
        channel_id (str | None): The channel id for the resource (optional).
        messages (list[dict] | None): The messages for the resource (optional).
    """

    realtime_resource_type: RealtimeResourceType
    knowledge_base_id: str
    url: str | None = None
    connection_params: dict[str, Any] | None = None
    db_type: DbType | None = None