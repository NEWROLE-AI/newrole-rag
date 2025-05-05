from aws_lambda_powertools import Logger
from opensearchpy import AsyncOpenSearch
from sqlalchemy.ext.asyncio import AsyncSession
from boto3_type_annotations.dynamodb import Client
from src.adapters.database.repositories.sql_repository import SqlAgentChatBotRepository
from src.adapters.database.repositories.dynamo_repository import (
    DynamoConversationRepository,
)
from src.adapters.database.repositories.opensearch_repository import (
    OpensearchVectorizedKnowledgeRepository,
)
from src.application.ports.unit_of_work import (
    UnitOfWork,
)


logger = Logger("sql_unit_of_work")


class UnitOfWorkImpl(UnitOfWork):
    """
    Implementation of the Unit of Work pattern for managing database transactions.

    Attributes:
        vectorized_knowledge (OpensearchVectorizedKnowledgeRepository): Repository for vectorized knowledge.
        agent_chat_bots (SqlAgentChatBotRepository): Repository for agent chat bots.
        conversations (DynamoConversationRepository): Repository for conversations.
    """

    vectorized_knowledge: OpensearchVectorizedKnowledgeRepository
    agent_chat_bots: SqlAgentChatBotRepository
    conversations: DynamoConversationRepository

    def __init__(
        self,
        session: AsyncSession,
        opensearch_client: AsyncOpenSearch,
        dynamo_client: Client,
        knn_parameter: int,
    ) -> None:
        """
        Initializes the Unit of Work with session and repository clients.

        Args:
            session (AsyncSession): The database session.
            opensearch_client (AsyncOpenSearch): The OpenSearch client for vectorized knowledge.
            dynamo_client (Client): The DynamoDB client for conversation management.
        """
        self._session = session
        self._opensearch_client = opensearch_client
        self._dynamo_client = dynamo_client
        self._knn_parameter = knn_parameter

    async def commit(self) -> None:
        """
        Commits the current transaction in the database.
        """
        logger.info("Committing transaction")
        await self._session.commit()

    async def __aenter__(self):
        """
        Begins a new unit of work, initializing repositories and returning the unit of work object.
        """
        logger.info("Starting new unit of work")
        self.agent_chat_bots = SqlAgentChatBotRepository(self._session)
        self.vectorized_knowledge = OpensearchVectorizedKnowledgeRepository(
            self._opensearch_client, self._knn_parameter
        )
        self.conversations = DynamoConversationRepository(self._dynamo_client)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Handles the cleanup at the end of the unit of work (either commit or rollback).

        Args:
            exc_type: The exception type.
            exc_val: The exception value.
            exc_tb: The exception traceback.
        """
        if exc_type:
            logger.error(f"Error occurred: {exc_val}")
        self.agent_chat_bots = None  # type: ignore
        self.vectorized_knowledge = None  # type: ignore
        self.conversations = None  # type: ignore
