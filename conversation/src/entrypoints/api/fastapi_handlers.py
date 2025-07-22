from fastapi import Depends, APIRouter
from dependency_injector.wiring import Provide, inject

from src.entrypoints.api.models import api_models
from src.entrypoints.api.ioc import FastapiContainer
from aws_lambda_powertools import Logger

from src.application.command_handlers.conversation import ConversationCommandHandler
from src.application.command_handlers.create_conversation import (
    CreateConversationCommandHandler,
)
from src.application.commands.conversation import ConversationCommand
from src.application.commands.create_conversation import CreateConversationCommand

# Initialize router and logger
router = APIRouter()
logger = Logger("fast_api_handlers")


@router.post("/v1/conversations/messages")
@inject
async def conversation(
    request: api_models.ConversationRequest,
    handler: ConversationCommandHandler = Depends(
        Provide[FastapiContainer.conversation_handler]
    ),
) -> api_models.ConversationResponse:
    """
    Handles incoming requests for conversations. The function takes a
    ConversationRequest, processes it using a ConversationCommandHandler, and
    returns a ConversationResponse.

    Args:
        request (api_models.ConversationRequest): The incoming conversation request.
        handler (ConversationCommandHandler): The command handler to process the request.

    Returns:
        api_models.ConversationResponse: The response containing conversation data.
    """
    logger.info(f"Received request for  conversation: {request}")

    # Create a command object from the request data
    command = ConversationCommand(**request.model_dump())
    logger.info(f"Created command: {command}")

    # Log the handler instance before execution
    logger.info(f"Handler instance before execution: {handler}")
    # Execute the handler with the created command
    result = await handler(command)
    logger.info("Handler execution completed")

    # Create the response from the result and return it
    response = api_models.ConversationResponse(**result)
    logger.info(f"Returning response: {response}")
    return response


# Lambda function for creating a conversation
@router.post("/v1/conversations")
@inject
async def create_conversation(
    request: api_models.CreateConversationRequest,
    handler: CreateConversationCommandHandler = Depends(
        Provide[FastapiContainer.create_conversation_handler]
    ),
) -> api_models.ConversationResponse:
    """
    Handles requests to create a new conversation. It uses the
    CreateConversationCommandHandler to process the request and return a
    ConversationResponse.

    Args:
        request (api_models.CreateConversationRequest): The request to create a conversation.
        handler (CreateConversationCommandHandler): The handler to process the creation.

    Returns:
        api_models.ConversationResponse: The response containing the newly created conversation's data.
    """
    logger.info(f"Received request for create conversation: {request}")
    # Create a command object from the request data
    command = CreateConversationCommand(**request.model_dump())
    logger.info(f"Created command: {command}")

    # Log the handler instance before execution
    logger.info(f"Handler instance before execution: {handler}")

    # Execute the handler with the created command
    result = await handler(command)
    logger.info("Handler execution completed")

    # Create the response from the result and return it
    response = api_models.CreateConversationResponse(**result)
    logger.info(f"Returning response: {response}")
    return response