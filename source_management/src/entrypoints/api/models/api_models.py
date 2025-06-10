from enum import Enum

from pydantic import BaseModel, Field
from src.application.models.realtime_resource import RealtimeResourceType, DbType
from src.application.models.vectorized_resource import VectorizedResourceType


class ResourceType(Enum):
    VECTORIZED = "VECTORIZED"
    REALTIME = "REALTIME"


class CreateResourceRequest(BaseModel):
    """
    Request model for creating a new resource.

    Attributes:
        knowledge_base_id (str): ID of the knowledge base
        resource_type (str): Type of resource to create
        file_type (str | None): Optional file type for the resource
        channel_id(str | None): Optional channel ID for the resource
        messages(list[dict] | None): Optional list of messages
    """

    knowledge_base_id: str
    resource_type: ResourceType
    vectorized_resource_type: VectorizedResourceType | None = None
    realtime_resource_type: RealtimeResourceType | None = None
    url: str | None = None
    db_type: DbType | None = None
    file_type: str | None = None
    channel_id: str | None = None
    messages: list[dict] | None = None
    query: str | None = None
    google_drive_url: str | None = None
    connection_params: dict[str, str | int] | None = None
    dynamodb_table_name: str | None = None


class CreateResourceResponse(BaseModel):
    """
    Response model for resource creation.

    Attributes:
        resource_id (str): ID of the resource
        presigned_url (str | None): URL for uploading the resource file
    """

    resource_id: str
    presigned_url: str | None = None


class CreateKnowledgeBaseRequest(BaseModel):
    """
    Request model for creating a new knowledge base.

    Attributes:
        knowledge_base_name (str): Name of the knowledge base
    """

    knowledge_base_name: str


class CreateKnowledgeBaseResponse(BaseModel):
    """
    Response model for knowledge base creation.

    Attributes:
        knowledge_base_id (str): ID of the created knowledge base
    """

    knowledge_base_id: str


class GetResourceIdsByKnowledgeBaseRequest(BaseModel):
    """
    Request model for retrieving resource IDs.

    Attributes:
        knowledge_base_id (str): ID of the knowledge base
    """

    knowledge_base_id: str


class GetResourceIdsByKnowledgeBaseResponse(BaseModel):
    """
    Response model containing list of resource IDs.

    Attributes:
        resource_ids (list[str]): List of resource IDs
    """

    resource_ids: list[str]


class GetAllResourcesRequest(BaseModel):
    """
    Request model for retrieving all resources.
    """

    pass


class GetAllResourcesResponse(BaseModel):
    """
    Response model for retrieving all resources.

    Attributes:
        knowledge_bases (list[dict]): List of knowledge bases
    """

    knowledge_bases: list[dict]

class DatabaseProperties(BaseModel):
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


class RestApiProperties(BaseModel):
    """
    Properties specific to a REST API resource.

    Attributes:
        method (str): HTTP method to use (e.g., "GET", "POST").
        header (dict[str, str] | None): Optional HTTP headers to include in the request.
        payload (dict[str, str] | None): Optional body payload for POST/PUT requests.
        query_params (dict[str, str] | None): Optional query parameters to include in the URL.
        placeholders (dict[str, str] | None): Optional placeholders to replace in the URL.
    """
    method: RestApiMethods
    header: dict[str, str] | None = None
    payload: dict[str, str] | None = None
    query_params: dict[str, str] | None = None
    placeholders: dict[str, str] | None = None


class RealtimeResource(BaseModel):
    """
    Represents a realtime resource, which can be either a database or a REST API.

    Attributes:
        resource_id (str): Unique identifier of the resource.
        resource_type (RealtimeResourceType): Type of the realtime resource.
        additional_properties (DatabaseProperties | RestApiProperties | None):
            Additional configuration based on the resource type.
    """
    resource_id: str
    knowledge_base_id: str | None = None
    resource_type: RealtimeResourceType
    additional_properties: DatabaseProperties | RestApiProperties | None = None


class VectorizationResource(BaseModel):
    """
    Represents a resource containing input data for vectorization.

    Attributes:
        resource_id (str): Unique identifier of the resource.
        input_data (str | None): Raw input data to be vectorized.
    """
    knowledge_base_id: str | None = None
    resource_id: str
    input_data: str | None = None


class GetDataRequest(BaseModel):
    """
    Request model for retrieving realtime and vectorization data.

    Attributes:
        realtime_resources (list[RealtimeResource]):
            List of realtime resources to fetch data from.
        vectorization_resources (list[VectorizationResource]):
            List of vectorization resources containing raw input data.
    """
    realtime_resources: list[RealtimeResource] | None = None
    vectorization_resources: list[VectorizationResource] | None = None


class GetDataResponse(BaseModel):
    realtime_responses: tuple[dict | None, ...] = Field(default_factory=tuple)
    vectorize_responses: tuple[dict | None, ...] = Field(default_factory=tuple)