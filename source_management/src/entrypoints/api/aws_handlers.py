import asyncio

from aws_lambda_powertools import Logger
from dependency_injector.wiring import inject, Provide, Closing

from src.adapters.query_service import DynamoQueryService
from src.application.command_handlers.create_knowledge_base import (
    CreateKnowledgeBaseCommandHandler,
)
from src.application.command_handlers.create_realtime_resource import CreateRealtimeResourceCommandHandler
from src.application.command_handlers.create_vectorized_resource import (
    CreateVectorizedResourceCommandHandler,
)
from src.application.command_handlers.get_realtime_data import GetRealtimeDataCommandHandler
from src.application.command_handlers.get_vectorized_data import GetVectorizedDataCommandHandler
from src.application.commands.create_knowledge_base import CreateKnowledgeBaseCommand
from src.application.commands.create_realtime_resource import CreateRealtimeResourceCommand
from src.application.commands.create_vectorized_resource import CreateVectorizedResourceCommand
from src.application.commands.get_realtime_data import GetRealtimeDataCommand
from src.application.commands.get_vectorized_data import GetVectorizedDataCommand
from src.application.ports.unit_of_work import UnitOfWork
from src.entrypoints.api.ioc import AwsContainer
from src.entrypoints.api.middleware.utils import lambda_handler_decorator
from src.entrypoints.api.models import api_models
from src.entrypoints.api.models.api_models import GetDataResponse, ResourceType


@lambda_handler_decorator(api_models.CreateResourceRequest)
@inject
async def create_resource(
    request: api_models.CreateResourceRequest,
    vectorized_resource_handler: CreateVectorizedResourceCommandHandler = Closing[
        Provide[AwsContainer.create_resource_handler]
    ],
    realtime_resource_handler: CreateRealtimeResourceCommandHandler = Closing[
        Provide[AwsContainer.create_realtime_resource_handler]
    ]
) -> api_models.CreateResourceResponse:
    """
    AWS Lambda handler for creating a new resource in a knowledge base.

    Args:
        request (CreateResourceRequest): Contains knowledge_base_id, resource_type and optional file_type
        vectorized_resource_handler (CreateVectorizedResourceCommandHandler): Injected handler for resource creation

    Returns:
        CreateResourceStaticFileResponse: Contains presigned URL for file upload

    Raises:
        ValidationError: If request data is invalid
        Exception: For any other errors during processing
    """
    logger.info(f"Received request for create_resource: {request}")
    # Create a command from the query data
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


@lambda_handler_decorator(api_models.CreateKnowledgeBaseRequest)
@inject
async def create_knowledge_base(
    request: api_models.CreateKnowledgeBaseRequest,
    handler: CreateKnowledgeBaseCommandHandler = Closing[
        Provide[AwsContainer.create_knowledge_base_handler]
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
    query_service: DynamoQueryService = Closing[Provide[AwsContainer.query_service]],
) -> api_models.GetResourceIdsByKnowledgeBaseResponse:
    """
    AWS Lambda handler for retrieving all resource IDs associated with a knowledge base.

    Args:
        request (GetResourceIdsByKnowledgeBaseRequest): Contains knowledge base ID
        query_service (DynamoQueryService): Injected query service for database operations

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
    query_service: DynamoQueryService = Closing[Provide[AwsContainer.query_service]],
) -> api_models.GetAllResourcesResponse:
    """
    AWS Lambda handler for retrieving all resources.

    Args:
        request (GetAllResourcesRequest): request
        query_service (DynamoQueryService): Injected query service for database operations

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


@lambda_handler_decorator(api_models.GetDataRequest)
@inject
async def retrieve_data(
    request: api_models.GetDataRequest,
    realtime_data_handler: GetRealtimeDataCommandHandler = Closing[Provide[AwsContainer.get_realtime_data_service]],
    vectorized_data_handler: GetVectorizedDataCommandHandler = Closing[Provide[AwsContainer.get_vectorized_data_service]]
) -> api_models.GetDataResponse:
    """
    AWS Lambda handler for retrieving all resources.

    Args:
        request (GetAllResourcesRequest): request
        query_service (DynamoQueryService): Injected query service for database operations

    Returns:
        GetAllResourcesResponse: Contains list of resources

    Raises:
        ValidationError: If request data is invalid
        Exception: For any other errors during processing
    """
    logger.info(f"Received request for get data: {request}")
    realtime_command = GetRealtimeDataCommand(request.realtime_resources)
    vectorized_command = GetVectorizedDataCommand(request.vectorization_resources)

    task_list = [realtime_data_handler(realtime_command), vectorized_data_handler(vectorized_command)]

    result = await asyncio.gather(*task_list)

    return GetDataResponse (
        realtime_responses = result[0],
        vectorize_responses = result[1]
    )


@lambda_handler_decorator(api_models.GetResourcesByKnowledgeBaseIdRequest)
@inject
async def retrieve_data(
    request: api_models.GetResourcesByKnowledgeBaseIdRequest,
    unit_of_work: UnitOfWork = Closing[Provide[AwsContainer.unit_of_work]]
) -> api_models.GetResourcesByKnowledgeBaseIdResponse:
    async with unit_of_work as uow:
        resource_info = await uow.resources.get_by_knowledge_base_id(request.knowledge_base_id)
    return api_models.GetResourcesByKnowledgeBaseIdResponse(resource_info=resource_info)


# Initializing the logger and dependency container
logger = Logger("handlers")
container = AwsContainer()
container.wire(modules=[__name__])
