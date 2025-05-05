from aws_lambda_powertools import Logger
from dependency_injector.wiring import inject, Provide, Closing

from src.adapters.query_service import QueryService
from src.application.command_handlers.create_knowledge_base import (
    CreateKnowledgeBaseCommandHandler,
)
from src.application.command_handlers.create_resource import (
    CreateResourceCommandHandler,
)
from src.application.commands.create_knowledge_base import CreateKnowledgeBaseCommand
from src.application.commands.create_resource import CreateResourceCommand
from src.application.models.resource import ResourceType
from src.entrypoints.api.ioc import Container
from src.entrypoints.api.middleware.utils import lambda_handler_decorator
from src.entrypoints.api.models import api_models


@lambda_handler_decorator(api_models.CreateResourceRequest)
@inject
async def create_resource(
    request: api_models.CreateResourceRequest,
    handler: CreateResourceCommandHandler = Closing[
        Provide[Container.create_resource_handler]
    ],
) -> api_models.CreateResourceResponse:
    """
    AWS Lambda handler for creating a new resource in a knowledge base.

    Args:
        request (CreateResourceRequest): Contains knowledge_base_id, resource_type and optional file_type
        handler (CreateResourceCommandHandler): Injected handler for resource creation

    Returns:
        CreateResourceStaticFileResponse: Contains presigned URL for file upload

    Raises:
        ValidationError: If request data is invalid
        Exception: For any other errors during processing
    """
    logger.info(f"Received request for create_resource: {request}")
    # Create a command from the query data
    command = CreateResourceCommand(
        **request.model_dump(exclude_none=True),
    )
    logger.info(f"Created command: {command}")
    logger.info(f"Handler instance before execution: {handler}")
    result = await handler(command)
    logger.info(f"Handler execution result: {result}")
    response = api_models.CreateResourceResponse(**result)
    logger.info(f"Returning response: {response}")
    return response


@lambda_handler_decorator(api_models.CreateKnowledgeBaseRequest)
@inject
async def create_knowledge_base(
    request: api_models.CreateKnowledgeBaseRequest,
    handler: CreateKnowledgeBaseCommandHandler = Closing[
        Provide[Container.create_knowledge_base_handler]
    ],
) -> api_models.CreateKnowledgeBaseResponse:
    """
    AWS Lambda handler for creating a new knowledge base.

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


@lambda_handler_decorator(api_models.GetResourceIdsByKnowledgeBaseRequest)
@inject
async def get_resource_ids_by_knowledge_base_id(
    request: api_models.GetResourceIdsByKnowledgeBaseRequest,
    query_service: QueryService = Closing[Provide[Container.query_service]],
) -> api_models.GetResourceIdsByKnowledgeBaseResponse:
    """
    AWS Lambda handler for retrieving all resource IDs associated with a knowledge base.

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


@lambda_handler_decorator(api_models.GetAllResourcesRequest)
@inject
async def get_all_resources(
    request: api_models.GetAllResourcesRequest,
    query_service: QueryService = Closing[Provide[Container.query_service]],
) -> api_models.GetAllResourcesResponse:
    """
    AWS Lambda handler for retrieving all resources.

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


# Initializing the logger and dependency container
logger = Logger("handlers")
container = Container()
container.wire(modules=[__name__])
