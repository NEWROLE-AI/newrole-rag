from datetime import datetime

from src.application.models.conversation import Conversation, Message
from src.application.ports.unit_of_work import ConversationRepository
from boto3_type_annotations.dynamodb import ServiceResource


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
        self._conversations = self._dynamo_client.Table("Conversations-dev")

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
