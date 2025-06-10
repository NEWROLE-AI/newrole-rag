import fastapi
from dependency_injector.wiring import Closing, Provide, inject

from src.adapters.query_service import QueryService
from src.application.command_handlers.create_knowledge_base import CreateKnowledgeBaseCommandHandler
from src.application.command_handlers.create_vectorized_resource import CreateVectorizedResourceCommandHandler
from src.application.commands.create_knowledge_base import CreateKnowledgeBaseCommand
from src.application.commands.create_vectorized_resource import CreateVectorizedResourceCommand
from src.entrypoints.api.ioc import FastapiContainer
from src.entrypoints.api.models import api_models

from fastapi.logger import logger

router = fastapi.APIRouter()

from fastapi import Depends

@router.post("/v1/resources")
@inject
async def create_resource(
    request: api_models.CreateResourceRequest,
    handler: CreateVectorizedResourceCommandHandler = Depends(
        Provide[FastapiContainer.create_resource_handler]
    ),
) -> api_models.CreateResourceResponse:
    """
    FastAPI handler for creating a new resource in a knowledge base.

    Args:
        request (CreateResourceRequest): Contains knowledge_base_id, resource_type and optional file_type
        handler (CreateVectorizedResourceCommandHandler): Injected handler for resource creation

    Returns:
        CreateResourceStaticFileResponse: Contains presigned URL for file upload

    Raises:
        ValidationError: If request data is invalid
        Exception: For any other errors during processing
    """
    logger.info(f"Received request for create_resource: {request}")
    # Create a command from the query data
    command = CreateVectorizedResourceCommand(
        **request.model_dump(exclude_none=True),
    )
    logger.info(f"Created command: {command}")
    logger.info(f"Handler instance before execution: {handler}")
    result = await handler(command)
    logger.info(f"Handler execution result: {result}")
    response = api_models.CreateResourceResponse(**result)
    logger.info(f"Returning response: {response}")
    return response


@router.post("/v1/knowledge_bases")
@inject
async def create_knowledge_base(
    request: api_models.CreateKnowledgeBaseRequest,
    handler: CreateKnowledgeBaseCommandHandler = Depends(
        Closing[Provide[FastapiContainer.create_knowledge_base_handler]]
    ),
) -> api_models.CreateKnowledgeBaseResponse:
    """
    FastAPI handler for creating a new knowledge base.

    Args:
        request (CreateKnowledgeBaseRequest): Contains knowledge base name
        handler (CreateKnowledgeBaseCommandHandler): Injected handler for knowledge base creation

    Returns:
        CreateKnowledgeBaseResponse: Contains ID of created knowledge base

    Raises:
        ValidationError: If request data is invalid
        Exception: For any other errors during processing
    """
    logger.info(f"Received request for create_knowledge_base: {request}")
    # Create a command from the name of the knowledge base
    command = CreateKnowledgeBaseCommand(
        knowledge_base_name=request.knowledge_base_name
    )
    logger.info(f"Created command: {command}")
    logger.info(f"Handler instance before execution: {handler}")
    result = await handler(command)
    logger.info("Handler execution completed")
    response = api_models.CreateKnowledgeBaseResponse(**result)
    logger.info(f"Returning response: {response}")
    return response

@router.get("/v1/resources")
@inject
async def get_resource_ids_by_knowledge_base_id(
    request: api_models.GetResourceIdsByKnowledgeBaseRequest,
    query_service: QueryService = Depends(Closing[Provide[FastapiContainer.query_service]]),
) -> api_models.GetResourceIdsByKnowledgeBaseResponse:
    """
    FAstAPI handler for retrieving all resource IDs associated with a knowledge base.

    Args:
        request (GetResourceIdsByKnowledgeBaseRequest): Contains knowledge base ID
        query_service (QueryService): Injected query service for database operations

    Returns:
        GetResourceIdsByKnowledgeBaseResponse: Contains list of resource IDs

    Raises:
        ValidationError: If request data is invalid
        Exception: For any other errors during processing
    """
    logger.info(f"Received request for get resource ids: {request}")
    result = await query_service.get_resource_ids_by_knowledge_base_id(
        request.knowledge_base_id
    )
    logger.info("Query service execution completed")
    response = api_models.GetResourceIdsByKnowledgeBaseResponse(**result)
    logger.info(f"Returning response: {response}")
    return response

@router.get("/v1/resources/all")
@inject
async def get_all_resources(
    request: api_models.GetAllResourcesRequest,
    query_service: QueryService = Depends(Closing[Provide[FastapiContainer.query_service]]),
) -> api_models.GetAllResourcesResponse:
    """
    FastAPI handler for retrieving all resources.

    Args:
        request (GetAllResourcesRequest): request
        query_service (QueryService): Injected query service for database operations

    Returns:
        GetAllResourcesResponse: Contains list of resources

    Raises:
        ValidationError: If request data is invalid
        Exception: For any other errors during processing
    """
    logger.info(f"Received request for get all resources: {request}")
    result = await query_service.get_all_resources()
    response = api_models.GetAllResourcesResponse(knowledge_bases=result)
    logger.info(f"Returning response with {len(result)} knowledge bases")
    return response

# Initializing dependency container
container = FastapiContainer()
container.wire(modules=[__name__])