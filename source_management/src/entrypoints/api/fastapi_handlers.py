
@router.post("/v1/users")
@inject
async def create_user(
    user_data: dict,
    unit_of_work = Depends(Provide["unit_of_work"])
):
    async with unit_of_work as uow:
        existing_user = await uow.users.get_by_id(user_data["user_id"])
        if existing_user:
            return {"message": "User already exists"}
        
        user = User(
            id=user_data["user_id"],
            email=user_data["email"],
            display_name=user_data.get("display_name", "")
        )
        await uow.users.create(user)
        await uow.commit()
        return {"message": "User created successfully"}

@router.get("/v1/knowledge-bases")
@inject
async def get_user_knowledge_bases(
    x_user_id: str = Header(..., alias="X-User-ID"),
    unit_of_work = Depends(Provide["unit_of_work"])
):
    async with unit_of_work as uow:
        knowledge_bases = await uow.knowledge_bases.get_by_user_id(x_user_id)
        return {"knowledge_bases": knowledge_bases}


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

from fastapi import Depends

@router.post("/v1/resources")
@inject
async def create_resource(
    request: api_models.CreateResourceRequest,
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
        vectorized_resource_handler (CreateVectorizedResourceCommandHandler): Injected handler for vectorized resource creation
        realtime_resource_handler (CreateRealtimeResourceCommandHandler): Injected handler for realtime resource creation

    Returns:
        CreateResourceStaticFileResponse: Contains presigned URL for file upload

    Raises:
        ValidationError: If request data is invalid
        Exception: For any other errors during processing
    """
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

@router.get("/v1/resources/{knowledge_base_id}")
@inject
async def get_resource_ids_by_knowledge_base_id(
    knowledge_base_id: str,
    query_service: DynamoQueryService = Depends(Closing[Provide[FastapiContainer.query_service]]),
) -> api_models.GetResourceIdsByKnowledgeBaseResponse:
    """
    FAstAPI handler for retrieving all resource IDs associated with a knowledge base.

    Args:
        knowledge_base_id (str): knowledge base ID
        query_service (DynamoQueryService): Injected query service for database operations

    Returns:
        GetResourceIdsByKnowledgeBaseResponse: Contains list of resource IDs

    Raises:
        ValidationError: If request data is invalid
        Exception: For any other errors during processing
    """
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
) -> api_models.GetAllResourcesResponse:
    """
    FastAPI handler for retrieving all resources.

    Args:
        query_service (DynamoQueryService): Injected query service for database operations

    Returns:
        GetAllResourcesResponse: Contains list of resources

    Raises:
        ValidationError: If request data is invalid
        Exception: For any other errors during processing
    """
    logger.info(f"Received request for get all resources.")
    result = await query_service.get_all_resources()
    response = api_models.GetAllResourcesResponse(knowledge_bases=result)
    logger.info(f"Returning response with {len(result)} knowledge bases")
    return response

# Initializing dependency container
container = FastapiContainer()
container.wire(modules=[__name__])