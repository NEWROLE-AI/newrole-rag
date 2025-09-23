import os
import uuid
from datetime import datetime
from decimal import Decimal

from src.application.models.conversation import Conversation, Message
from src.application.ports.unit_of_work import ConversationRepository, BackgroundCheckRepository
from boto3_type_annotations.dynamodb import ServiceResource
from motor.motor_asyncio import AsyncIOMotorDatabase


class DynamoConversationRepository(ConversationRepository):
    """
    Repository implementation for storing and retrieving conversation data using DynamoDB.

    Inherits from ConversationRepository and provides methods to interact with a DynamoDB table
    for storing and retrieving conversation records.

    Attributes:
        _dynamo_client (ServiceResource): The DynamoDB client used for interacting with DynamoDB service.
        _conversations (DynamoDB.Table): The DynamoDB table for storing conversations.
    """

    def __init__(self, dynamo_client: ServiceResource):
        """
        Initializes the DynamoConversationRepository with a DynamoDB client.

        Args:
            dynamo_client (ServiceResource): The DynamoDB client used for accessing the service.
        """
        self._dynamo_client = dynamo_client
        env = os.environ.get("ENVIRONMENT")
        self._conversations = self._dynamo_client.Table(f"Conversations-{env}")

    async def save(self, conversation: Conversation):
        """
        Saves a conversation to the DynamoDB table.

        Converts the Conversation object into a dictionary and stores it in the DynamoDB table.

        Args:
            conversation (Conversation): The conversation object to be saved.
        """
        self._conversations.put_item(Item=conversation.to_dict())

    async def get(self, conversation_id: str) -> Conversation | None:
        """
        Retrieves a conversation from the DynamoDB table by its ID.

        Args:
            conversation_id (str): The ID of the conversation to retrieve.

        Returns:
            Conversation: The retrieved Conversation object.

        Raises:
            ValueError: If the conversation with the given ID is not found.
        """
        response = self._conversations.get_item(
            Key={"conversation_id": conversation_id}
        )
        if "Item" not in response:
            return None
        item = response["Item"]
        return Conversation.from_dict(item)


class DynamoBackgroundCheckRepository(BackgroundCheckRepository):
    """
    Repository implementation for storing background check data using DynamoDB.

    Inherits from BackgroundRepository and provides methods to interact with a DynamoDB table
    for storing conversation records.

    Attributes:
        _dynamo_client (ServiceResource): The DynamoDB client used for interacting with DynamoDB service.
        _background_checks (DynamoDB.Table): The DynamoDB table for storing conversations.
    """

    def __init__(self, dynamo_client: ServiceResource):
        """
        Initializes the DynamoConversationRepository with a DynamoDB client.

        Args:
            dynamo_client (ServiceResource): The DynamoDB client used for accessing the service.
        """
        self._dynamo_client = dynamo_client
        env = os.environ.get("ENVIRONMENT")
        self._background_checks = self._dynamo_client.Table(f"BackgroundCheck-{env}")

    async def save(self, user_id: str, background_check: dict):
        """
        Saves a conversation to the DynamoDB table.

        Converts the Conversation object into a dictionary and stores it in the DynamoDB table.

        Args:
            background_check (dict): The conversation object to be saved.
        """

        def convert_floats_to_decimal(data):
            if isinstance(data, dict):
                return {key: convert_floats_to_decimal(value) for key, value in data.items()}
            elif isinstance(data, list):
                return [convert_floats_to_decimal(item) for item in data]
            elif isinstance(data, float):
                return Decimal(str(data))  # Convert float to Decimal
            else:
                return data

        background_check = convert_floats_to_decimal(background_check)
        request_id = str(uuid.uuid4())
        self._background_checks.put_item(Item={"request_id": request_id, "user_id": user_id, "data": background_check})
        return request_id


class MongoConversationRepository(ConversationRepository):
    """
    Repository implementation for storing and retrieving conversation data using MongoDB.

    Inherits from ConversationRepository and provides methods to interact with a MongoDB collection
    for storing and retrieving conversation records.

    Attributes:
        _database (AsyncIOMotorDatabase): The MongoDB database instance.
        _conversations: The MongoDB collection for storing conversations.
    """

    def __init__(self, database: AsyncIOMotorDatabase):
        """
        Initializes the MongoConversationRepository with a MongoDB database.

        Args:
            database (AsyncIOMotorDatabase): The MongoDB database instance.
        """
        self._database = database
        collection_name = f"conversations"
        self._conversations = self._database[collection_name]

    async def save(self, conversation: Conversation):
        """
        Saves a conversation to the MongoDB collection.
        Uses update_one with upsert for better compatibility.
        """
        conversation_dict = conversation.to_dict()

        # Заменяем replace_one на update_one с $set
        await self._conversations.update_one(
            {"conversation_id": conversation_dict["conversation_id"]},
            {"$set": conversation_dict},
            upsert=True
        )

    async def get(self, conversation_id: str) -> Conversation | None:
        """
        Retrieves a conversation from the MongoDB collection by its ID.

        Args:
            conversation_id (str): The ID of the conversation to retrieve.

        Returns:
            Optional[Conversation]: The retrieved Conversation object or None if not found.
        """
        document = await self._conversations.find_one(
            {"conversation_id": conversation_id}
        )

        if not document:
            return None

        # Remove MongoDB's _id field if present
        document.pop("_id", None)
        return Conversation.from_dict(document)

    async def get_by_user_id(self, user_id: str) -> list[Conversation]:
        documents = await self._conversations.find(
            {"user_id": user_id}
        ).to_list()

        for document in documents:
            document.pop("_id", None)

        return [Conversation.from_dict(document) for document in documents]

    async def delete(self, conversation_id: str):
        """
        Deletes a conversation and raises exception if not found.
        """
        if hasattr(self._conversations, 'delete_one'):
            result = await self._conversations.delete_one(
                {"conversation_id": conversation_id}
            )
            if result.deleted_count == 0:
                raise ValueError(f"Conversation with id {conversation_id} not found")
            return True
        else:
            result = await self._conversations.remove(
                {"conversation_id": conversation_id}
            )
            if result.get("n", 0) == 0:
                raise ValueError(f"Conversation with id {conversation_id} not found")
            return True


    async def get_messages(self, conversation_id: str) -> list[Message]:
        if hasattr(self._conversations, 'find_one'):
            document = await self._conversations.find_one(
                {"conversation_id": conversation_id}
            )
        else:
            document = await self._conversations.find_one(
                {"conversation_id": conversation_id}
            )

        if not document:
            return []

        # Убираем MongoDB _id поле
        document.pop("_id", None)

        try:
            # Предполагаем, что Conversation имеет поле messages
            conversation = Conversation.from_dict(document)
            return conversation.messages if hasattr(conversation, 'messages') else []
        except Exception as e:
            return []