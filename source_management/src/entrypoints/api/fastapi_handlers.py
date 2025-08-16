import fastapi
from dependency_injector.wiring import Closing, Provide, inject

from src.adapters.query_service import DynamoQueryService
from src.application.command_handlers.create_knowledge_base import CreateKnowledgeBaseCommandHandler
from src.application.command_handlers.create_realtime_resource import CreateRealtimeResourceCommandHandler
from src.application.command_handlers.create_vectorized_resource import CreateVectorizedResourceCommandHandler
from src.application.commands.create_knowledge_base import CreateKnowledgeBaseCommand
from src.application.commands.create_realtime_resource import CreateRealtimeResourceCommand
from src.application.commands.create_vectorized_resource import CreateVectorizedResourceCommand
from src.entrypoints.api.ioc import FastapiContainer
from src.entrypoints.api.models import api_models

from fastapi.logger import logger

from src.entrypoints.api.models.api_models import ResourceType

router = fastapi.APIRouter()

from fastapi import Depends, Header
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.adapters.database.db import get_async_session
from src.adapters.database.models import User, KnowledgeBase
from src.application.command_handlers.get_vectorized_data import (
    GetVectorizedDataCommandHandler,
)
from src.application.commands.get_vectorized_data import GetVectorizedDataCommand

async def get_current_user(
    x_user_id: Optional[str] = Header(None),
    session: AsyncSession = Depends(get_async_session)
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
    session: AsyncSession = Depends(get_async_session)
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

@router.get("/api/v1/knowledge-bases")
async def get_knowledge_bases(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Get user's knowledge bases"""
    result = await session.execute(
        select(KnowledgeBase).where(KnowledgeBase.user_id == current_user.id)
    )
    knowledge_bases = result.scalars().all()
    return [{"id": kb.id, "name": kb.name, "description": kb.description, "created_at": kb.created_at} for kb in knowledge_bases]

@router.post("/api/v1/knowledge-bases", response_model=CreateKnowledgeBaseResponse)
async def create_knowledge_base(
    request: CreateKnowledgeBaseRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Create a new knowledge base for the current user"""
    knowledge_base = KnowledgeBase(
        name=request.name,
        description=request.description,
        user_id=current_user.id
    )
    session.add(knowledge_base)
    await session.commit()
    return CreateKnowledgeBaseResponse(knowledge_base_id=knowledge_base.id)


@router.post("/v1/resources")
@inject
async def create_resource(
    request: api_models.CreateResourceRequest,
    vectorized_resource_handler: CreateVectorizedResourceCommandHandler = Depends(Closing[
        Provide[FastapiContainer.create_resource_handler]
    ]),
    realtime_resource_handler: CreateRealtimeResourceCommandHandler = Depends(Closing[
        Provide[FastapiContainer.create_realtime_resource_handler]
    ]),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
    uow=Depends(get_unit_of_work)
) -> api_models.CreateResourceResponse:
    """
    FastAPI handler for creating a new resource in a knowledge base.

    Args:
        request (CreateResourceRequest): Contains knowledge_base_id, resource_type and optional file_type
        vectorized_resource_handler (CreateVectorizedResourceCommandHandler): Injected handler for vectorized resource creation
        realtime_resource_handler (CreateRealtimeResourceCommandHandler): Injected handler for realtime resource creation
        current_user (User): The currently authenticated user.
        session (AsyncSession): The database session.
        uow: Unit of work for command handling.

    Returns:
        CreateResourceStaticFileResponse: Contains presigned URL for file upload

    Raises:
        ValidationError: If request data is invalid
        Exception: For any other errors during processing
    """
    # Verify knowledge base belongs to user
    result = await session.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.id == request.knowledge_base_id,
            KnowledgeBase.user_id == current_user.id
        )
    )
    knowledge_base = result.scalar_one_or_none()
    if not knowledge_base:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    if request.resource_type == ResourceType.VECTORIZED:
        command = CreateVectorizedResourceCommand(
            **request.model_dump(exclude_none=True, exclude={"resource_type"}),
        )
        logger.info(f"Created command: {command}")
        logger.info(f"Handler instance before execution: {vectorized_resource_handler}")
        result = await vectorized_resource_handler(command)
        logger.info(f"Handler execution result: {result}")
        response = api_models.CreateResourceResponse(**result)
        logger.info(f"Returning response: {response}")
    elif request.resource_type == ResourceType.REALTIME:
        command = CreateRealtimeResourceCommand(
            **request.model_dump(exclude_none=True, exclude={"resource_type"}),
        )
        logger.info(f"Created command: {command}")
        logger.info(f"Handler instance before execution: {realtime_resource_handler}")
        result = await realtime_resource_handler(command)
        logger.info(f"Handler execution result: {result}")
        response = api_models.CreateResourceResponse(**result)
        logger.info(f"Returning response: {response}")
    else:
        raise Exception("Invalid resource type")
    return response


@router.get("/v1/resources/{knowledge_base_id}")
@inject
async def get_resource_ids_by_knowledge_base_id(
    knowledge_base_id: str,
    query_service: DynamoQueryService = Depends(Closing[Provide[FastapiContainer.query_service]]),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
) -> api_models.GetResourceIdsByKnowledgeBaseResponse:
    """
    FastAPI handler for retrieving all resource IDs associated with a knowledge base.

    Args:
        knowledge_base_id (str): knowledge base ID
        query_service (DynamoQueryService): Injected query service for database operations
        current_user (User): The currently authenticated user.
        session (AsyncSession): The database session.

    Returns:
        GetResourceIdsByKnowledgeBaseResponse: Contains list of resource IDs

    Raises:
        ValidationError: If request data is invalid
        Exception: For any other errors during processing
    """
    # Verify knowledge base belongs to user
    result = await session.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.id == knowledge_base_id,
            KnowledgeBase.user_id == current_user.id
        )
    )
    knowledge_base = result.scalar_one_or_none()
    if not knowledge_base:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    logger.info(f"Received request for get resource ids: {knowledge_base_id}")
    result = await query_service.get_resource_ids_by_knowledge_base_id(
        knowledge_base_id
    )
    logger.info("Query service execution completed")
    response = api_models.GetResourceIdsByKnowledgeBaseResponse(**result)
    logger.info(f"Returning response: {response}")
    return response

@router.get("/v1/resources/all")
@inject
async def get_all_resources(
    query_service: DynamoQueryService = Depends(Closing[Provide[FastapiContainer.query_service]]),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    FastAPI handler for retrieving all resources.

    Args:
        query_service (DynamoQueryService): Injected query service for database operations
        current_user (User): The currently authenticated user.
        session (AsyncSession): The database session.

    Returns:
        GetAllResourcesResponse: Contains list of resources

    Raises:
        ValidationError: If request data is invalid
        Exception: For any other errors during processing
    """
    # This endpoint might need to be refactored to return resources per user
    # For now, we'll fetch all resources and assume they are accessible by the user.
    # A more robust solution would filter by user_id.
    logger.info(f"Received request for get all resources.")
    result = await query_service.get_all_resources()
    response = api_models.GetAllResourcesResponse(knowledge_bases=result)
    logger.info(f"Returning response with {len(result)} knowledge bases")
    return response

@router.post("/api/v1/data/retrieve")
async def retrieve_data(
    request: GetVectorizedDataRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
    uow=Depends(get_unit_of_work)
):
    """Retrieve data from user's knowledge base"""
    # Verify knowledge base belongs to user
    result = await session.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.id == request.knowledge_base_id,
            KnowledgeBase.user_id == current_user.id
        )
    )
    knowledge_base = result.scalar_one_or_none()
    if not knowledge_base:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    command = GetVectorizedDataCommand(
        knowledge_base_id=request.knowledge_base_id,
        vectorization_resources=request.vectorization_resources,
        realtime_resources=request.realtime_resources,
    )
    handler = GetVectorizedDataCommandHandler(uow=uow)
    data = await handler.handle(command=command)
    return data


# Initializing dependency container
container = FastapiContainer()
container.wire(modules=[__name__])