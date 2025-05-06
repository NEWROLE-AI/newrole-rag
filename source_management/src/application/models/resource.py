from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any


class ResourceType(str, Enum):
    """Enum defining the possible types of resources."""

    STATIC_FILE = "STATIC_FILE"
    SLACK_CHANNEL = "SLACK_CHANNEL"
    DATABASE = "DATABASE"
    GOOGLE_DRIVE = "GOOGLE_DRIVE"
    DYNAMODB_TABLE = "DYNAMODB_TABLE"

class DictFormatMixin:

    @classmethod
    def timestamp_dict_factory(cls, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return obj

    def to_dict(self) -> dict:
        return asdict(self, dict_factory=DictFormatMixin.timestamp_dict_factory)

    @classmethod
    def from_dict(cls, data: dict) -> Any:
        return cls(**data) if data else None

@dataclass
class Resource(DictFormatMixin):
    """
    Represents a resource within a Knowledge Base.

    Resources can be of various types (e.g., STATIC_FILE) and are associated with a knowledge base.

    Attributes:
        resource_id (str): The unique identifier for the resource.
        knowledge_base_id (str): The ID of the knowledge base to which the resource belongs.
        type (ResourceType): The type of resource (e.g., STATIC_FILE).
        extra (SlackChannel | File | None): Extra information about the resource.
    """

    resource_id: str
    knowledge_base_id: str
    type: ResourceType
    extra: SlackChannel | File | Database | GoogleDrive | DynamodbTable | None = None

    @classmethod
    def from_dict(cls, data: dict) -> Resource:
        extra_data = data.get("extra", {})
        resource_type = data.get('type')

        dataclass_type = RESOURCE_TYPE_MAP.get(resource_type)

        extra = dataclass_type.from_dict(extra_data) if dataclass_type and extra_data else None

        return cls(
            resource_id=data.get("resource_id"),
            knowledge_base_id=data.get("knowledge_base_id"),
            type=ResourceType(data.get("type")),
            extra=extra
        )


@dataclass
class GoogleDrive(DictFormatMixin):
    google_drive_url: str

@dataclass
class File(DictFormatMixin):
    extension: str

@dataclass
class Database(DictFormatMixin):
    connection_params: dict[str, str]
    query: str

@dataclass
class SlackChannel(DictFormatMixin):
    """
    Represents an extra within a Resource.

    Attributes:
        channel_id (str): The unique identifier for the channel id.
        messages (list[SlackMessage]): The messages that are in the channel.
    """

    channel_id: str
    messages: list[SlackMessage]

    @classmethod
    def from_dict(cls, data: dict) -> SlackChannel:
        messages_data = data.get('messages', [])
        messages = [SlackMessage.from_dict(msg) for msg in messages_data]
        return cls(channel_id=data.get('channel_id'), messages=messages)

@dataclass
class SlackMessage(DictFormatMixin):
    """
    Represents a message within a SlackChannel.

    Attributes:
        message_id (str): The unique identifier for the message id.
        content (str): The text message.
        user_id (str): The unique identifier for the user in slack id.
        timestamp (datetime): The timestamp of the message.
    """

    message_id: str
    content: str
    user_id: str
    timestamp: datetime | None = None

    @classmethod
    def from_dict(cls, data: dict) -> SlackMessage:
        timestamp_str = data.get('timestamp')
        timestamp = datetime.fromisoformat(timestamp_str) if timestamp_str else None
        return cls(
            message_id=data.get("message_id"),
            content=data.get("content"),
            user_id=data.get("user_id"),
            timestamp=timestamp
        )


@dataclass
class DynamodbTable:
    table_name: str


RESOURCE_TYPE_MAP: dict[str, type] = {
    ResourceType.SLACK_CHANNEL.value: SlackChannel,
    ResourceType.STATIC_FILE.value: File,
    ResourceType.DATABASE.value: Database,
    ResourceType.GOOGLE_DRIVE.value: GoogleDrive,
    ResourceType.DYNAMODB_TABLE.value: DynamodbTable,
}