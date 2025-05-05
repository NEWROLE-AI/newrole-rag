from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.models.agent_chat_bot import AgentChatBot, Prompt
from src.application.ports.unit_of_work import AgentChatBotRepository


class SqlAgentChatBotRepository(AgentChatBotRepository):
    """
    Repository implementation for managing agent chat bots using SQL (PostgreSQL or other relational databases).

    Inherits from AgentChatBotRepository and provides methods to interact with the database for storing and retrieving
    agent chat bot and prompt data.

    Attributes:
        _session (AsyncSession): The SQLAlchemy async session used for database operations.
    """

    def __init__(self, session: AsyncSession):
        """
        Initializes the SqlAgentChatBotRepository with an async session.

        Args:
            session (AsyncSession): The SQLAlchemy async session used for database operations.
        """
        self._session = session

    async def get(self, agent_chat_bot_id: str) -> AgentChatBot:
        """
        Retrieves an agent chat bot and its associated prompt from the database by its ID.

        Args:
            agent_chat_bot_id (str): The ID of the agent chat bot to retrieve.

        Returns:
            AgentChatBot: The retrieved agent chat bot object.

        Raises:
            ValueError: If the agent chat bot with the given ID is not found.
        """

        # SQL query to get agent chat bot by ID
        agent_query = text(
            "SELECT * FROM agent_chat_bots WHERE agent_chat_bot_id = :id"
        )
        agent_result = await self._session.execute(
            agent_query, {"id": agent_chat_bot_id}
        )

        # Fetch the agent row from the result
        agent_row = agent_result.fetchone()

        # SQL query to get prompt by ID
        prompt_query = text(
            """
            SELECT * FROM prompts WHERE id = :id
            """
        )
        prompt_result = await self._session.execute(prompt_query, {"id": agent_row.id})
        prompt_row = prompt_result.fetchone()
        if not agent_row:
            raise ValueError(f"AgentChatBot with ID {agent_chat_bot_id} not found")

        # Return the agent chat bot and its associated prompt
        return AgentChatBot(
            agent_chat_bot_id=agent_row.agent_chat_bot_id,
            knowledge_base_id=agent_row.knowledge_base_id,
            prompt=Prompt(prompt_id=prompt_row.prompt_id, text=prompt_row.text),
        )
