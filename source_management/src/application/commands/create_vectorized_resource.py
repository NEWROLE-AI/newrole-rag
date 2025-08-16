from dataclasses import dataclass

from src.application.commands.base import BaseCommand
from src.application.models.vectorized_resource import VectorizedResourceType


@dataclass
class CreateVectorizedResourceCommand(BaseCommand):
    """
    Command for creating a resource (e.g., static file).

    This command contains data about the resource to be created, such as its type,
    the associated knowledge base, and the file type.

    Attributes:
        vectorized_resource_type (VectorizedResourceType): The type of the resource (e.g., STATIC_FILE).
        knowledge_base_id (str): The ID of the knowledge base associated with the resource.
        file_type (str | None): The type of file for the resource (optional).
        channel_id (str | None): The channel id for the resource (optional).
        messages (list[dict] | None): The messages for the resource (optional).
    """

    vectorized_resource_type: VectorizedResourceType
    knowledge_base_id: str
    channel_id: str | None = None
    file_type: str | None = None
    messages: list[dict] | None = None
    connection_params: dict[str, str] | None = None
    query: str | None = None
    google_drive_url: str | None = None
    dynamodb_table_name: str | None = None
