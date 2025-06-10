from dataclasses import dataclass
from enum import Enum

from src.application.commands.base import BaseCommand
from src.application.models.realtime_resource import RealtimeResourceType


@dataclass
class DatabaseProperties:
    """
    Properties specific to a database resource.

    Attributes:
        query (str): SQL query to be executed against the database.
    """
    query: str

class RestApiMethods(Enum):
    """
    Enum representing HTTP methods for REST API resources.
    """
    GET = "GET"
    POST = "POST"


@dataclass
class RestApiProperties:
    """
    Properties specific to a REST API resource.

    Attributes:
        method (str): HTTP method to use (e.g., "GET", "POST").
        header (dict[str, str] | None): Optional HTTP headers to include in the request.
        payload (dict[str, str] | None): Optional body payload for POST/PUT requests.
        query_params (dict[str, str] | None): Optional query parameters to include in the URL.
        placeholders (dict[str, str] | None): Optional placeholders for dynamic values in the query.
    """
    method: RestApiMethods
    header: dict[str, str] | None
    payload: dict[str, str] | None
    query_params: dict[str, str] | None
    placeholders: dict[str, str] | None


@dataclass
class RealtimeResource:
    """
    Represents a realtime resource, which can be either a database or a REST API.

    Attributes:
        resource_id (str): Unique identifier of the resource.
        resource_type (RealtimeResourceType): Type of the realtime resource.
        additional_properties (DatabaseProperties | RestApiProperties | None):
            Additional configuration based on the resource type.
    """
    knowledge_base_id: str
    resource_id: str
    resource_type: RealtimeResourceType
    additional_properties: DatabaseProperties | RestApiProperties | None

@dataclass
class GetRealtimeDataCommand(BaseCommand):
    realtime_resource: list[RealtimeResource]