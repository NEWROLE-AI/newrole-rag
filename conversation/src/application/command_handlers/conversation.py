import uuid

from aws_lambda_powertools import Logger

from admin_panel.src.adapters.database.models import knowledge_bases
from src.application.command_handlers.base import BaseCommandHandler
from src.application.commands.conversation import ConversationCommand
from src.application.models.conversation import Message, Conversation
from src.application.ports.ai_service import AIService
from src.application.ports.api_client import (
    SourceManagementApiClient,
    VectorizerApiClient,
)
from src.application.ports.unit_of_work import UnitOfWork

logger = Logger("conversation_handler")


class ConversationCommandHandler(BaseCommandHandler):
    """
    Command handler for processing a conversation request.

    This handler processes a `ConversationCommand`, which contains a message and a conversation ID.
    The handler interacts with the conversation repository, the AI service, and other required
    services to fetch or generate the appropriate response.

    Attributes:
        _unit_of_work (UnitOfWork): Handles interactions with the database repositories.
        _source_management_api_client (SourceManagementApiClient): Client for fetching knowledge base resources.
        _ai_service (AIService): Service for generating AI responses.
        _vectorizer (VectorizerApiClient): Client for vectorizing text messages.
    """

    def __init__(
        self,
        unit_of_work: UnitOfWork,
        source_management_api_client: SourceManagementApiClient,
        ai_service: AIService,
        vectorizer_api_client: VectorizerApiClient,
    ):
        """
        Initializes the conversation command handler with dependencies.

        Args:
            unit_of_work (UnitOfWork): The unit of work for managing transactions.
            source_management_api_client (SourceManagementApiClient): Client for interacting with source management.
            ai_service (AIService): Service to generate AI responses.
            vectorizer_api_client (VectorizerApiClient): Client for vectorizing text.
        """
        self._unit_of_work = unit_of_work
        self._source_management_api_client = source_management_api_client
        self._ai_service = ai_service
        self._vectorizer = vectorizer_api_client

    async def __call__(self, command: ConversationCommand):
        """
        Handles the conversation command by processing the user input, generating a response,
        and updating the conversation.

        Args:
            command (ConversationCommand): The command object containing the user message and conversation ID.

        Returns:
            dict: The response containing the conversation ID and the generated response message.
        """
        logger.info(f"Handling command {command}")
        async with self._unit_of_work as uow:
            # Fetch the conversation from the database
            conversation = await uow.conversations.get(command.conversation_id)
            if not conversation:
                conversation = Conversation(
                    conversation_id=command.conversation_id,
                    agent_chat_bot_id="013ce799-00c2-47da-beaa-3690dd9d28a7",
                    messages=[],
                )
                await uow.conversations.save(conversation)
            logger.info(f"Handling conversation {conversation}")

            # Create a new message from the user input
            user_message = Message(
                message_id=str(uuid.uuid4()),
                content=command.message,
                role="user",
                user_id=command.user_id,
            )
            conversation.messages.append(user_message)

            # Fetch the agent details associated with the conversation
            agent = await uow.agent_chat_bots.get(conversation.agent_chat_bot_id)

            resource_info = await self._source_management_api_client.get_resource_info_by_knowledge_base_id(agent.knowledge_base_id)

            source_management_query_body = await self._ai_service.generate_api_response(
                conversation.messages, agent.knowledge_base_id, resource_info
            )

            resource_data = await self._source_management_api_client.get_data(request_body=source_management_query_body)

            message = await self._ai_service.generate_response_with_resources(
                prompt=agent.prompt,
                resource_data=resource_data,
                messages=conversation.messages,
            )

            agent_message = Message(
                message_id=str(uuid.uuid4()),
                content=message,
                role="assistant",
                user_id="assistant",
            )

            conversation.messages.append(agent_message)

            await uow.conversations.save(conversation)

            return {
                "conversation_id": conversation.conversation_id,
                "message": message,
            }

            # ====================================================================================
            # sql_query = await self._ai_service.generate_sql_response(
            #     command.message
            # )
            #
            # # Retrieve knowledge from the vectorized knowledge base
            # knowledge_base = await uow.execute(sql_query)
            # logger.info("knowledge base get success", extra={"knowledge_base": knowledge_base})
            # # Generate a response using the AI service
            # message, payload = await self._ai_service.generate_response(
            #     prompt=agent.prompt,
            #     vectorized_knowledge_base=knowledge_base,
            #     messages=conversation.messages,
            # )
            # if payload:
            #     if any(key != "data_ready" for key in payload):
            #         logger.info("Save background check")
            #         request_id = await uow.background_checks.save(command.user_id, payload)
            #         message += f" Request_id: {request_id}"
            #     else:
            #         logger.warning("Payload contains only 'data_ready', skipping save")
            # # Create a message for the agent's response
            # agent_message = Message(
            #     message_id=str(uuid.uuid4()),
            #     content=message,
            #     role="assistant",
            #     user_id="assistant",
            # )
            # conversation.messages.append(agent_message)
            #
            # # Save the updated conversation to the database
            # await uow.conversations.save(conversation)
            #
            # # Return the response as a dictionary
            # return {
            #     "conversation_id": conversation.conversation_id,
            #     "message": message,
            # }
