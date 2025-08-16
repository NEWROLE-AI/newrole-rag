from fastapi import Depends, APIRouter, Header, HTTPException
from dependency_injector.wiring import Provide, inject
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from src.entrypoints.api.models import api_models
from src.entrypoints.api.ioc import FastapiContainer
from aws_lambda_powertools import Logger

from src.adapters.database.sql_db import User, Conversation, Message, get_session
from src.application.command_handlers.conversation import ConversationCommandHandler
from src.application.command_handlers.create_conversation import (
    CreateConversationCommandHandler,
)
from src.application.commands.conversation import ConversationCommand
from src.application.commands.create_conversation import CreateConversationCommand

# Initialize router and logger
router = APIRouter()
logger = Logger("fast_api_handlers")


async def get_current_user(
    x_user_id: Optional[str] = Header(None),
    session: AsyncSession = Depends(get_session)
) -> User:
    """Get current user from X-User-ID header"""
    if not x_user_id:
        raise HTTPException(status_code=401, detail="User ID header missing")

    result = await session.execute(select(User).where(User.id == x_user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/api/v1/users")
async def create_user(
    user_data: dict,
    session: AsyncSession = Depends(get_session)
):
    """Create a new user"""
    user = User(
        id=user_data["user_id"],
        username=user_data.get("display_name", ""),
        email=user_data["email"]
    )
    session.add(user)
    await session.commit()
    return {"message": "User created successfully"}

@router.get("/api/v1/conversations")
async def get_conversations(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Get user's conversations"""
    result = await session.execute(
        select(Conversation).where(Conversation.user_id == current_user.id)
    )
    conversations = result.scalars().all()
    return [{"id": c.id, "title": c.title, "created_at": c.created_at} for c in conversations]


# Lambda function for creating a conversation
@router.post("/api/v1/conversations", response_model=api_models.CreateConversationResponse)
@inject
async def create_conversation(
    request: api_models.CreateConversationRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    handler: CreateConversationCommandHandler = Depends(
        Provide[FastapiContainer.create_conversation_handler]
    ),
):
    """
    Handles requests to create a new conversation for the current user.
    It uses the CreateConversationCommandHandler to process the request and return a
    ConversationResponse.

    Args:
        request (api_models.CreateConversationRequest): The request to create a conversation.
        current_user (User): The currently authenticated user.
        session (AsyncSession): The database session.
        handler (CreateConversationCommandHandler): The handler to process the creation.

    Returns:
        api_models.CreateConversationResponse: The response containing the newly created conversation's data.
    """
    logger.info(f"Received request for create conversation: {request}")

    # Create a conversation entity associated with the user
    conversation = Conversation(
        title=getattr(request, 'title', 'New Conversation'),
        user_id=current_user.id
    )
    session.add(conversation)
    await session.commit()

    # Create a command object from the request data
    command = CreateConversationCommand(**request.model_dump(), conversation_id=conversation.id)
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


@router.post("/api/v1/conversations/{conversation_id}/messages")
@inject
async def send_message(
    conversation_id: str,
    request: api_models.ConversationRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    handler: ConversationCommandHandler = Depends(
        Provide[FastapiContainer.conversation_handler]
    ),
):
    """
    Handles incoming requests for conversations with user validation.
    The function takes a ConversationRequest, processes it using a ConversationCommandHandler, and
    returns a ConversationResponse.

    Args:
        conversation_id (str): The ID of the conversation.
        request (api_models.ConversationRequest): The incoming conversation request.
        current_user (User): The currently authenticated user.
        session (AsyncSession): The database session.
        handler (ConversationCommandHandler): The command handler to process the request.

    Returns:
        api_models.ConversationResponse: The response containing conversation data.
    """
    logger.info(f"Received request for conversation: {request}")

    # Verify conversation belongs to user
    result = await session.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id
        )
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Add user message
    user_message = Message(
        conversation_id=conversation_id,
        content=request.message,
        role="user"
    )
    session.add(user_message)
    await session.commit()

    # Process conversation through existing handler
    command = ConversationCommand(**request.model_dump())
    logger.info(f"Created command: {command}")

    # Log the handler instance before execution
    logger.info(f"Handler instance before execution: {handler}")
    # Execute the handler with the created command
    result = await handler(command)
    logger.info("Handler execution completed")

    # Add assistant response
    assistant_message = Message(
        conversation_id=conversation_id,
        content=result.get("response", ""),
        role="assistant"
    )
    session.add(assistant_message)
    await session.commit()

    # Create the response from the result and return it
    response = api_models.ConversationResponse(**result)
    logger.info(f"Returning response: {response}")
    return response