from pydantic import BaseModel

from src.application.models.resource import ResourceType


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
    file_type: str | None = None
    channel_id: str | None = None
    messages: list[dict] | None = None
    query: str | None = None
    google_drive_url: str | None = None
    connection_params: dict[str, str] | None = None
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
