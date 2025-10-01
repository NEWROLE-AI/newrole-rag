"""
API Gateway Models

Consolidated models for all API interactions within the gateway.
This file contains all models from admin_panel, conversation, and source_management services
to avoid cross-service dependencies and ensure the API Gateway is self-contained.
"""

import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


# ========== ADMIN PANEL MODELS ==========

class CreatePromptRequest(BaseModel):
    text: str


class CreatePromptResponse(BaseModel):
    prompt_id: str


class CreateAgentChatBotRequest(BaseModel):
    name: str
    knowledge_base_id: str | None = None
    prompt_id: str


class CreateAgentChatBotResponse(BaseModel):
    agent_chat_bot_id: str


class ChangeSettingsAgentChatBotRequest(BaseModel):
    agent_chat_bot_id: str
    knowledge_base_id: str | None = None
    prompt_id: str | None = None


class UpdatePromptTextRequest(BaseModel):
    prompt_id: str
    text: str = ""


class UpdatePromptTextResponse(BaseModel):
    message: str = "Success"


class ChangeSettingsAgentChatBotResponse(BaseModel):
    agent_chat_bot_id: str


# GET Response Models for Admin Panel
class Prompt(BaseModel):
    id: str
    prompt_id: str
    text: str


class GetPromptsResponse(BaseModel):
    prompts: list[Prompt]


class Chatbot(BaseModel):
    id: str
    agent_chat_bot_id: str
    name: str
    prompt_id: str | None = None
    knowledge_base_id: str | None = None
    user_id: str


class GetChatbotsResponse(BaseModel):
    chatbots: list[Chatbot]


class DeleteResponse(BaseModel):
    message: str = "Deleted successfully"


# ========== CONVERSATION MODELS ==========

class ConversationRequest(BaseModel):
    """
    Model for the incoming request to fetch a conversation.

    Attributes:
        conversation_id (str): The unique ID of the conversation.
        message (str): The message within the conversation.
    """
    conversation_id: str
    message: str


class ConversationResponse(BaseModel):
    """
    Model for the response containing conversation details.

    Attributes:
        conversation_id (str): The unique ID of the conversation.
        message (str): The message within the conversation.
    """
    conversation_id: str
    message: str


class CreateConversationRequest(BaseModel):
    """
    Model for the incoming request to create a new conversation.

    Attributes:
        agent_chat_bot_id (str): The ID of the agent chat bot initiating the conversation.
    """
    agent_chat_bot_id: str


class CreateConversationResponse(BaseModel):
    """
    Model for the response containing the newly created conversation's details.

    Attributes:
        conversation_id (str): The unique ID of the newly created conversation.
    """
    conversation_id: str


class GetConversationResponse(BaseModel):
    class Conversation(BaseModel):
        conversation_id: str
        agent_chat_bot_id: str

    conversation_list: list[Conversation]


class GetMessagesResponse(BaseModel):
    class Message(BaseModel):
        message_id: str
        role: str
        content: str
        timestamp: datetime.datetime

    messages: list[Message]


# ========== SOURCE MANAGEMENT MODELS ==========

# Enums for Source Management
class ResourceType(str, Enum):
    VECTORIZED = "VECTORIZED"
    REALTIME = "REALTIME"


class VectorizedResourceType(str, Enum):
    """Enum defining the possible types of vectorized resources."""
    STATIC_FILE = "STATIC_FILE"
    SLACK_CHANNEL = "SLACK_CHANNEL"
    DATABASE = "DATABASE"
    GOOGLE_DRIVE = "GOOGLE_DRIVE"
    DYNAMODB_TABLE = "DYNAMODB_TABLE"


class RealtimeResourceType(str, Enum):
    """
    Enum representing types of realtime resources.

    - DATABASE: A connection to a relational database.
    - REST_API: A RESTful API endpoint.
    """
    DATABASE = "DATABASE"
    REST_API = "REST_API"


class DbType(str, Enum):
    POSTGRESQL = "POSTGRESQL"
    MYSQL = "MYSQL"


class RestApiMethods(str, Enum):
    """
    Enum representing HTTP methods for REST API resources.
    """
    GET = "GET"
    POST = "POST"


# Source Management Request/Response Models
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
    knowledge_base_id: str | None = None
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


class GetResourceIdsByKnowledgeBaseResponse(BaseModel):
    """
    Response model containing list of resource IDs.

    Attributes:
        resource_ids (list[str]): List of resource IDs
    """
    resource_ids: list[str]


class GetAllResourcesResponse(BaseModel):
    """
    Response model for retrieving all resources.

    Attributes:
        knowledge_bases (list[dict]): List of knowledge bases
    """
    resource_list: list[dict]


class GetKnowledgeBasesResponse(BaseModel):
    """
    Response model for retrieving all knowledge bases.

    Attributes:
        knowledge_bases (list[dict]): List of knowledge bases
    """
    class KnowledgeBase(BaseModel):
        knowledge_base_id: str
        name: str
        user_id: str

    knowledge_bases: list[KnowledgeBase]


class DatabaseProperties(BaseModel):
    """
    Properties specific to a database resource.

    Attributes:
        query (str): SQL query to be executed against the database.
    """
    query: str


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


class GetResourcesByKnowledgeBaseIdRequest(BaseModel):
    knowledge_base_id: str


class GetResourcesByKnowledgeBaseIdResponse(BaseModel):
    resource_info: list[dict]


# ========== ADDITIONAL RESPONSE MODELS ==========

# Fix for conversation response - ensuring consistency
class GetConversationsResponse(BaseModel):
    """Alternative name for consistency with UI expectations"""
    conversations: list[GetConversationResponse.Conversation]


# Response model aliases for UI compatibility
class GetResourcesResponse(BaseModel):
    """Response model with resources key for UI compatibility"""
    resources: list[dict]


class GetKnowledgeBasesWithResourcesResponse(BaseModel):
    """Enhanced knowledge bases response with resources"""
    knowledge_bases: list[dict]