import asyncio

import fastapi
from dependency_injector.wiring import Closing, Provide, inject
from starlette import status

from src.adapters.query_service import DynamoQueryService, MongoQueryService
from src.application.command_handlers.create_knowledge_base import CreateKnowledgeBaseCommandHandler
from src.application.command_handlers.create_realtime_resource import CreateRealtimeResourceCommandHandler
from src.application.command_handlers.create_vectorized_resource import CreateVectorizedResourceCommandHandler
from src.application.commands.create_knowledge_base import CreateKnowledgeBaseCommand
from src.application.commands.create_realtime_resource import CreateRealtimeResourceCommand
from src.application.commands.create_vectorized_resource import CreateVectorizedResourceCommand

from src.application.commands.get_realtime_data import GetRealtimeDataCommand
from src.application.commands.get_vectorized_data import GetVectorizedDataCommand

from src.application.command_handlers.get_realtime_data import GetRealtimeDataCommandHandler
from src.application.command_handlers.get_vectorized_data import GetVectorizedDataCommandHandler
from src.application.exceptions.authentication_exception import AuthenticationException
from src.application.ports.unit_of_work import UnitOfWork
from src.entrypoints.api.ioc import FastapiContainer
from src.entrypoints.api.models import api_models

from fastapi.logger import logger

from src.entrypoints.api.models.api_models import ResourceType

router = fastapi.APIRouter()

from fastapi import Depends, Header, HTTPException


@router.post("/v1/resources")
@inject
async def create_resource(
    request: api_models.CreateResourceRequest,
    user_id: str = Header(alias="X-User-ID"),
    vectorized_resource_handler: CreateVectorizedResourceCommandHandler = Depends(Closing[
        Provide[FastapiContainer.create_resource_handler]
    ]),
    realtime_resource_handler: CreateRealtimeResourceCommandHandler = Depends(Closing[
        Provide[FastapiContainer.create_realtime_resource_handler]
    ])
) -> api_models.CreateResourceResponse:
    """
    FastAPI handler for creating a new resource in a knowledge base.

    Args:
        request (CreateResourceRequest): Contains knowledge_base_id, resource_type and optional file_type
        headers (dict): Request headers containing user_id
        vectorized_resource_handler (CreateVectorizedResourceCommandHandler): Injected handler for vectorized resource creation
        realtime_resource_handler (CreateRealtimeResourceCommandHandler): Injected handler for realtime resource creation

    Returns:
        CreateResourceStaticFileResponse: Contains presigned URL for file upload

    Raises:
        ValidationError: If request data is invalid
        Exception: For any other errors during processing
    """
    try:
        if request.resource_type == ResourceType.VECTORIZED:
            command = CreateVectorizedResourceCommand(
                **request.model_dump(exclude_none=True, exclude={"resource_type"}),
                user_id=user_id
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
                user_id=user_id
            )
            logger.info(f"Created command: {command}")
            logger.info(f"Handler instance before execution: {realtime_resource_handler}")
            result = await realtime_resource_handler(command)
            logger.info(f"Handler execution result: {result}")
            response = api_models.CreateResourceResponse(**result)
            logger.info(f"Returning response: {response}")
        else:
            raise Exception("Invalid resource type")
    except AuthenticationException as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    return response


@router.post("/v1/knowledge-bases")
@inject
async def create_knowledge_base(
    request: api_models.CreateKnowledgeBaseRequest,
    user_id: str = Header(alias="X-User-ID"),
    handler: CreateKnowledgeBaseCommandHandler = Depends(
        Closing[Provide[FastapiContainer.create_knowledge_base_handler]]
    ),
) -> api_models.CreateKnowledgeBaseResponse:
    """
    FastAPI handler for creating a new knowledge base.

    Args:
        request (CreateKnowledgeBaseRequest): Contains knowledge base name
        headers (dict): Request headers containing user_id
        handler (CreateKnowledgeBaseCommandHandler): Injected handler for knowledge base creation

    Returns:
        CreateKnowledgeBaseResponse: Contains ID of created knowledge base

    Raises:
        ValidationError: If request data is invalid
        Exception: For any other errors during processing
    """

    logger.info(f"Received request for create_knowledge_base: {request}")
    # Create a command from the name of the knowledge base with user_id
    command = CreateKnowledgeBaseCommand(
        knowledge_base_name=request.knowledge_base_name,
        user_id=user_id
    )
    logger.info(f"Created command: {command}")
    logger.info(f"Handler instance before execution: {handler}")
    result = await handler(command)
    logger.info("Handler execution completed")
    response = api_models.CreateKnowledgeBaseResponse(**result)
    logger.info(f"Returning response: {response}")
    return response


@router.get("/v1/resources/all")
@inject
async def get_all_resources(
    user_id: str = Header(alias="X-User-ID"),
    query_service: MongoQueryService = Depends(Closing[Provide[FastapiContainer.query_service]]),
    unit_of_work: UnitOfWork = Depends(Closing[Provide[FastapiContainer.unit_of_work]]),
) -> api_models.GetAllResourcesResponse:
    """
    FastAPI handler for retrieving all resources for the current user.

    Args:
        headers (dict): Request headers containing user_id
        query_service (DynamoQueryService): Injected query service for database operations

    Returns:
        GetAllResourcesResponse: Contains list of resources

    Raises:
        ValidationError: If request data is invalid
        Exception: For any other errors during processing
    """

    async with unit_of_work as uow:
        knowledge_base_list = await uow.knowledge_bases.get_list_by_id(user_id)

    logger.info(f"Received request for get all resources by user_id: {user_id}")
    result = await query_service.get_all_resources([knowledge_base.knowledge_base_id for knowledge_base in knowledge_base_list])
    response = api_models.GetAllResourcesResponse(resource_list=result)
    logger.info(f"Returning response with {len(result)} knowledge bases")
    return response

@router.get("/v1/resources/{knowledge_base_id}")
@inject
async def get_resource_ids_by_knowledge_base_id(
    knowledge_base_id: str,
    user_id: str = Header(alias="X-User-ID"),
    query_service: MongoQueryService = Depends(Closing[Provide[FastapiContainer.query_service]]),
    unit_of_work: UnitOfWork = Depends(Closing[Provide[FastapiContainer.unit_of_work]]),
) -> api_models.GetResourceIdsByKnowledgeBaseResponse:
    """
    FAstAPI handler for retrieving all resource IDs associated with a knowledge base.

    Args:
        knowledge_base_id (str): knowledge base ID
        headers (dict): Request headers containing user_id
        query_service (DynamoQueryService): Injected query service for database operations

    Returns:
        GetResourceIdsByKnowledgeBaseResponse: Contains list of resource IDs

    Raises:
        ValidationError: If request data is invalid
        Exception: For any other errors during processing
    """
    logger.info(f"Received request for get resource ids: {knowledge_base_id}, user_id: {user_id}")

    async with unit_of_work as uow:
        knowledge_base = await uow.knowledge_bases.get(knowledge_base_id)

        if knowledge_base.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="This User is not owner of knowledge base")

    result = await query_service.get_resource_ids_by_knowledge_base_id(
        knowledge_base_id
    )
    logger.info("Query service execution completed")
    response = api_models.GetResourceIdsByKnowledgeBaseResponse(**result)
    logger.info(f"Returning response: {response}")
    return response

@router.get("/v1/knowledge-bases")
@inject
async def get_knowledge_bases(
    user_id: str = Header(alias="X-User-ID"),
    query_service: DynamoQueryService = Depends(Closing[Provide[FastapiContainer.query_service]]),
    unit_of_work: UnitOfWork = Depends(Closing[Provide[FastapiContainer.unit_of_work]]),
) -> api_models.GetKnowledgeBasesResponse:
    """
    FastAPI handler for retrieving all knowledge bases for the current user.

    Args:
        headers (dict): Request headers containing user_id
        query_service (DynamoQueryService): Injected query service for database operations

    Returns:
        GetKnowledgeBasesResponse: Contains list of knowledge bases

    Raises:
        ValidationError: If request data is invalid
        Exception: For any other errors during processing
    """

    logger.info(f"Received request for get knowledge bases for user: {user_id}")

    async with unit_of_work as uow:
        knowledge_base_list = await uow.knowledge_bases.get_list_by_id(user_id)

    response = api_models.GetKnowledgeBasesResponse(knowledge_bases=[api_models.GetKnowledgeBasesResponse.KnowledgeBase(
        knowledge_base_id=knowledge_base.knowledge_base_id,
        name=knowledge_base.name,
        user_id=knowledge_base.user_id,
    ) for knowledge_base in knowledge_base_list])
    logger.info(f"Returning response with {len(knowledge_base_list)} knowledge bases")
    return response


# DELETE Endpoints
@router.delete("/v1/knowledge-bases/{kb_id}")
@inject
async def delete_knowledge_base(
    kb_id: str,
    user_id: str = Header(alias="X-User-ID"),
    unit_of_work: UnitOfWork = Depends(Closing[Provide[FastapiContainer.unit_of_work]]),
) -> dict:
    """Delete knowledge base by ID"""
    logger.info(f"Deleting knowledge base {kb_id} for user: {user_id}")
    
    try:
        async with unit_of_work as uow:
            # Check if knowledge base belongs to user and delete
            kb = await uow.knowledge_bases.get(kb_id)
            if kb and kb.user_id == user_id:
                await uow.knowledge_bases.delete(kb_id)
            else:
                raise HTTPException(status_code=404, detail="Knowledge base not found or access denied")
    except Exception as e:
        logger.error(f"Error deleting knowledge base: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    return {"message": f"Knowledge base {kb_id} deleted successfully"}


@router.delete("/v1/resources/{resource_id}")
@inject
async def delete_resource(
    resource_id: str,
    user_id: str = Header(alias="X-User-ID"),
    unit_of_work: UnitOfWork = Depends(Closing[Provide[FastapiContainer.unit_of_work]]),
) -> dict:
    """Delete resource by ID"""
    logger.info(f"Deleting resource {resource_id} for user: {user_id}")
    
    try:
        async with unit_of_work as uow:
            # Check if resource belongs to user and delete
            resource = await uow.resources.get(resource_id)
            if resource and resource.user_id == user_id:
                await uow.resources.delete(resource_id)
            else:
                raise HTTPException(status_code=404, detail="Resource not found or access denied")
    except Exception as e:
        logger.error(f"Error deleting resource: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    return {"message": f"Resource {resource_id} deleted successfully"}


@router.post("/v1/data", response_model=api_models.GetDataResponse)
@inject
async def retrieve_data(
        request: api_models.GetDataRequest,
        realtime_data_handler: GetRealtimeDataCommandHandler = Depends(Provide[FastapiContainer.get_realtime_data_service]),
        vectorized_data_handler: GetVectorizedDataCommandHandler = Depends(
            Provide[FastapiContainer.get_vectorized_data_service])
) -> api_models.GetDataResponse:
    """
    FastAPI endpoint for retrieving all resources.

    Args:
        request (GetDataRequest): Request payload
        realtime_data_handler: Injected handler for realtime data operations
        vectorized_data_handler: Injected handler for vectorized data operations

    Returns:
        GetDataResponse: Contains realtime and vectorized responses

    Raises:
        ValidationError: If request data is invalid
        HTTPException: For any errors during processing
    """
    logger.info(f"Received request for get data: {request}")

    realtime_command = GetRealtimeDataCommand(request.realtime_resources)
    vectorized_command = GetVectorizedDataCommand(request.vectorization_resources)

    task_list = [
        realtime_data_handler(realtime_command),
        vectorized_data_handler(vectorized_command)
    ]

    result = await asyncio.gather(*task_list)

    return api_models.GetDataResponse(
        realtime_responses=result[0],
        vectorize_responses=result[1]
    )


# Initializing dependency container
container = FastapiContainer()
container.wire(modules=[__name__])
