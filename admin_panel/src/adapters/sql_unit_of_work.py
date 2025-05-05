from aws_lambda_powertools import Logger
from sqlalchemy import update, select, delete, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.models.agent_chat_bot import AgentChatBot
from src.application.models.prompt import Prompt
from src.application.ports.unit_of_work import (
    UnitOfWork,
    PromptRepository,
    AgentChatBotRepository,
)


logger = Logger("sql_unit_of_work")


class SqlAgentChatBotRepository(AgentChatBotRepository):
    """
    Repository implementation for managing agent chat bots using SQL database.

    This repository handles all database operations related to agent chat bots,
    including creation, retrieval, and updates.

    Attributes:
        _session (AsyncSession): The SQLAlchemy async session for database operations.
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Initializes the SqlAgentChatBotRepository with an async session.

        Args:
            session (AsyncSession): The SQLAlchemy async session for database operations.
        """
        self._session = session

    async def add(self, agent_chat_bot: AgentChatBot) -> None:
        """
        Adds a new agent chat bot to the database.

        This method first verifies that the associated prompt exists in the database
        before creating the agent chat bot record.

        Args:
            agent_chat_bot (AgentChatBot): The agent chat bot object to be added.

        Raises:
            ValueError: If the associated prompt does not exist in the database.
        """
        logger.info(f"Adding agent chat bot: {agent_chat_bot}")
        # First, verify prompt exists and get its internal ID
        get_prompt_id_query = text(
            """
                    SELECT id FROM prompts
                    WHERE prompt_id = :prompt_id
                """
        )
        result = await self._session.execute(
            get_prompt_id_query, {"prompt_id": agent_chat_bot.prompt_id}
        )
        row = result.fetchone()
        if not row:
            logger.error(f"Prompt with ID {agent_chat_bot.prompt_id} not found")
            raise ValueError(
                f"Prompt with ID {agent_chat_bot.prompt_id} does not exist"
            )
        prompt_id = row[0]

        # Insert the new agent chat bot
        insert_resource_query = text(
            """
                    INSERT INTO agent_chat_bots (name, agent_chat_bot_id, prompt_id, knowledge_base_id)
                    VALUES (:name, :agent_chat_bot_id, :prompt_id, :knowledge_base_id)
                """
        )
        await self._session.execute(
            insert_resource_query,
            {
                "name": agent_chat_bot.name,
                "agent_chat_bot_id": agent_chat_bot.agent_chat_bot_id,
                "knowledge_base_id": agent_chat_bot.knowledge_base_id,
                "prompt_id": prompt_id,
            },
        )
        logger.info(f"Agent {agent_chat_bot.agent_chat_bot_id} added successfully")

    async def get(self, agent_chat_bot_id: str) -> AgentChatBot:
        """
        Retrieves an agent chat bot from the database by its ID.

        Args:
            agent_chat_bot_id (str): The unique identifier of the agent chat bot.

        Returns:
            AgentChatBot: The retrieved agent chat bot object.

        Raises:
            ValueError: If no agent chat bot is found with the given ID.
        """
        logger.info(f"Fetching agent with ID: {agent_chat_bot_id}")
        query = text(
            """
                   SELECT name, knowledge_base_id, prompts.prompt_id
                   FROM agent_chat_bots
                   INNER JOIN prompts ON prompts.prompt_id = :prompt_id
                   WHERE agent_chat_bot_id = :agent_chat_bot_id
               """
        )
        result = await self._session.execute(
            query, {"agent_chat_bot_id": agent_chat_bot_id}
        )
        row = result.fetchone()
        if row:
            return AgentChatBot(
                name=row.name,
                agent_chat_bot_id=agent_chat_bot_id,
                knowledge_base_id=row.knowledge_base_id,
                prompt_id=row.prompt_id,
            )
        else:
            raise ValueError(f"Agent with ID {agent_chat_bot_id} not found")

    async def update(self, agent_chat_bot_id: str, **kwargs):
        """
        Updates an existing agent chat bot in the database.

        Args:
            agent_chat_bot_id (str): The ID of the agent chat bot to update.
            **kwargs: Key-value pairs of fields to update.

        Raises:
            ValueError: If updating the prompt_id and the new prompt doesn't exist.
        """
        logger.info(f"Updating agent with ID: {agent_chat_bot_id}")
        # Handle prompt_id updates separately to verify prompt exists
        if "prompt_id" in kwargs:
            logger.info(f"Fetching prompt ID for prompt_id: {kwargs.get("prompt_id")}")

            query = text(
                """
                SELECT id FROM prompts
                WHERE prompt_id = :prompt_id
                """
            )
            result = await self._session.execute(
                query, {"prompt_id": kwargs.get("prompt_id")}
            )
            row = result.fetchone()
            if not row:
                logger.error(
                    f"Prompt with prompt_id {kwargs.get("prompt_id")} not found"
                )
                raise ValueError(
                    f"Prompt with prompt_id {kwargs.get("prompt_id")} does not exist"
                )
            kwargs["prompt_id"] = row[0]
        # Construct and execute update query
        set_clause = ", ".join([f"{key} = :{key}" for key in kwargs])
        query = text(
            f"""
                UPDATE agent_chat_bots
                SET {set_clause}
                WHERE agent_chat_bot_id = :agent_chat_bot_id
            """
        )
        params = {"agent_chat_bot_id": agent_chat_bot_id, **kwargs}
        await self._session.execute(query, params)


class SqlPromptRepository(PromptRepository):
    """
    Repository implementation for managing prompts using SQL database.

    This repository handles all database operations related to prompts,
    including creation and retrieval.

    Attributes:
        _session (AsyncSession): The SQLAlchemy async session for database operations.
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Initializes the SqlPromptRepository with an async session.

        Args:
            session (AsyncSession): The SQLAlchemy async session for database operations.
        """
        self._session = session

    async def add(self, prompt: Prompt) -> None:
        """
        Adds a new prompt to the database.

        Args:
            prompt (Prompt): The prompt object to be added.
        """
        logger.info(f"Adding prompt: {prompt}")
        query = text(
            """
                    INSERT INTO prompts (prompt_id, text)
                    VALUES (:prompt_id, :text)
                """
        )
        await self._session.execute(
            query,
            {
                "prompt_id": prompt.prompt_id,
                "text": prompt.text,
            },
        )

    async def get(self, prompt_id: str) -> Prompt:
        """
        Retrieves a prompt from the database by its ID.

        Args:
            prompt_id (str): The unique identifier of the prompt.

        Returns:
            Prompt: The retrieved prompt object.

        Raises:
            ValueError: If no prompt is found with the given ID.
        """
        logger.info(f"Fetching prompt with ID: {prompt_id}")
        query = text(
            """
                    SELECT text
                    FROM prompts
                    WHERE prompt_id = :prompt_id
                """
        )
        result = await self._session.execute(query, {"prompt_id": prompt_id})
        row = result.fetchone()
        if row:
            return Prompt(
                prompt_id=prompt_id,
                text=row[0],
            )
        else:
            raise ValueError(f"Prompt with ID {prompt_id} not found")

    async def update(self, prompt_id: str, **kwargs):
        """
        Updates an existing prompt in the database.

        Args:
            prompt_id (str): The ID of the prompt to update.
            **kwargs: Key-value pairs of fields to update.

        Raises:
            ValueError: If updating the prompt_id and the new prompt doesn't exist.
        """
        logger.info(f"Updating text for prompt with ID: {prompt_id}")

        # Verify prompt exists before update
        verify_query = text(
            """
            SELECT id FROM prompts
            WHERE prompt_id = :prompt_id
            """
        )
        result = await self._session.execute(
            verify_query, {"prompt_id": prompt_id}
        )
        row = result.fetchone()
        if not row:
            logger.error(f"Prompt with prompt_id {prompt_id} not found")
            raise ValueError(f"Prompt with prompt_id {prompt_id} does not exist")

        # Update prompt text
        update_query = text(
            """
            UPDATE prompts
            SET text = :text
            WHERE prompt_id = :prompt_id
            """
        )
        await self._session.execute(
            update_query,
            {
                "prompt_id": prompt_id,
                "text": kwargs.get("text", ""),
            }
        )
        logger.info(f"Successfully updated text for prompt: {prompt_id}")

class SqlUnitOfWork(UnitOfWork):
    """
    Implementation of the Unit of Work pattern for SQL database operations.

    This class manages database transactions and provides access to various
    repositories for data access.

    Attributes:
        agent_chat_bots (SqlAgentChatBotRepository): Repository for agent chat bot operations.
        prompts (SqlPromptRepository): Repository for prompt operations.
        session (AsyncSession): The SQLAlchemy async session for database operations.
    """

    agent_chat_bots: SqlAgentChatBotRepository
    prompts: SqlPromptRepository

    def __init__(self, session: AsyncSession) -> None:
        """
        Initializes the SqlUnitOfWork with an async session.

        Args:
            session (AsyncSession): The SQLAlchemy async session for database operations.
        """
        self.session = session

    async def commit(self) -> None:
        """
        Commits the current transaction to the database.
        """
        logger.info("Committing transaction")
        await self.session.commit()

    async def __aenter__(self):
        """
        Enters the context manager, initializing repositories.

        Returns:
            SqlUnitOfWork: The initialized unit of work instance.
        """
        logger.info("Starting new unit of work")
        self.agent_chat_bots = SqlAgentChatBotRepository(self.session)
        self.prompts = SqlPromptRepository(self.session)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Exits the context manager, cleaning up repositories.

        Args:
            exc_type: The type of the exception that was raised, if any.
            exc_val: The instance of the exception that was raised, if any.
            exc_tb: The traceback of the exception that was raised, if any.
        """
        if exc_type:
            logger.error(f"Error occurred: {exc_val}")
        self.agent_chat_bots = None  # type: ignore
        self.prompts = None  # type: ignore
