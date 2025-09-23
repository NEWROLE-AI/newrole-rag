from fastapi import Depends, APIRouter, Header
from fastapi.exceptions import HTTPException
from dependency_injector.wiring import Provide, inject, Closing

from src.application.exceptions.authentication_exception import AuthenticationException
from src.application.ports.unit_of_work import UnitOfWork
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
    user_id: str = Header(alias="X-User-ID"),
    unit_of_work: UnitOfWork = Depends(Closing[Provide[FastapiContainer.unit_of_work]]),
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
    async with unit_of_work as uow:
        user_conversations = await uow.conversations.get_by_user_id(user_id)

        if user_id not in {row.user_id for row in user_conversations}:
            raise HTTPException(status_code=403, detail="Don't have enough permissions")

    # Create a command object from the request data
    command = ConversationCommand(**request.model_dump(), user_id=user_id)
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
    user_id: str = Header(alias="X-User-ID"),
) -> api_models.CreateConversationResponse:
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
    command = CreateConversationCommand(**request.model_dump(), user_id=user_id)
    logger.info(f"Created command: {command}")

    # Log the handler instance before execution
    logger.info(f"Handler instance before execution: {handler}")

    # Execute the handler with the created command
    try:
        result = await handler(command)
    except AuthenticationException as e:
        raise HTTPException(status_code=403, detail=str(e))
    logger.info("Handler execution completed")

    # Create the response from the result and return it
    response = api_models.CreateConversationResponse(**result)
    logger.info(f"Returning response: {response}")
    return response


# GET Endpoints
@router.get("/v1/conversations")
@inject
async def get_conversations(
    user_id: str = Header(alias="X-User-ID"),
    unit_of_work: UnitOfWork = Depends(Closing[Provide[FastapiContainer.unit_of_work]]),
) -> api_models.GetConversationResponse:
    """Get all conversations for user"""
    logger.info(f"Getting conversations for user: {user_id}")
    
    async with unit_of_work as uow:
        result = await uow.conversations.get_by_user_id(user_id)

    return api_models.GetConversationResponse(
        conversation_list=[
            api_models.GetConversationResponse.Conversation(
                conversation_id=row.conversation_id,
                agent_chat_bot_id=row.agent_chat_bot_id
            )
            for row in result
        ]
    )


@router.get("/v1/conversations/{conversation_id}/messages")
@inject
async def get_messages(
    conversation_id: str,
    user_id: str = Header(alias="X-User-ID"),
    unit_of_work: UnitOfWork = Depends(Closing[Provide[FastapiContainer.unit_of_work]]),
) -> api_models.GetMessagesResponse:
    """Get messages for conversation"""
    logger.info(f"Getting messages for conversation {conversation_id}, user: {user_id}")

    async with unit_of_work as uow:
        messages = await uow.conversations.get_messages(conversation_id)

    return api_models.GetMessagesResponse(
        messages=[
            api_models.GetMessagesResponse.Message(
                **message.to_dict()
            )
            for message in messages
        ]
    )


# DELETE Endpoints
@router.delete("/v1/conversations/{conversation_id}")
@inject
async def delete_conversation(
    conversation_id: str,
    user_id: str = Header(alias="X-User-ID"),
    unit_of_work: UnitOfWork = Depends(Closing[Provide[FastapiContainer.unit_of_work]]),
) -> dict:
    """Delete conversation by ID"""
    logger.info(f"Deleting conversation {conversation_id} for user: {user_id}")

    async with unit_of_work as uow:
        user_conversations = await uow.conversations.get_by_user_id(user_id)

        if user_id not in {row.user_id for row in user_conversations}:
            raise HTTPException(status_code=403, detail="Don't have enough permissions")
        await uow.conversations.delete(conversation_id)


    # Would need to implement repository method for deletion
    return {"message": f"Conversation {conversation_id} deleted successfully"}