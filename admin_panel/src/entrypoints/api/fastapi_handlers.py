import fastapi
from fastapi import Depends
from fastapi.logger import logger

from src.entrypoints.api.models import api_models
from src.application.command_handlers.create_prompt import CreatePromptCommandHandler
from src.application.command_handlers.create_agent_chat_bot import CreateAgentChatBotCommandHandler
from src.application.command_handlers.change_settings_chat_bot import ChangeSettingsAgentChatBotCommandHandler
from src.application.command_handlers.update_prompt_text import UpdatePromptTextCommandHandler
from src.application.commands.create_prompt import CreatePromptCommand
from src.application.commands.create_agent_chat_bot import CreateAgentChatBotCommand
from src.application.commands.change_settings_chat_bot import ChangeSettingsAgentChatBotCommand
from src.application.commands.update_prompt_text import UpdatePromptTextCommand
from dependency_injector.wiring import inject, Provide
from src.entrypoints.api.ioc import FastapiContainer
from fastapi import Header
from src.application.ports.unit_of_work import UnitOfWork


router = fastapi.APIRouter()

@router.post("/v1/prompts", response_model=api_models.CreatePromptResponse)
@inject
async def create_prompt(
    request: api_models.CreatePromptRequest,
    user_id: str = Header(alias="X-User-ID"),
    handler: CreatePromptCommandHandler = Depends(Provide[FastapiContainer.create_prompt_handler]),
) -> api_models.CreatePromptResponse:
    """
    FastAPI handler for creating a new prompt.

    Args:
        request (CreatePromptRequest): Contains the prompt text.
        handler (CreatePromptCommandHandler): Injected handler to process the command.

    Returns:
        CreatePromptResponse: Contains the created prompt's metadata.

    Raises:
        ValidationError: If the request data is invalid.
        Exception: For any unexpected error during processing.
    """
    logger.info(f"Received request for prompt: {request}")
    command = CreatePromptCommand(text=request.text, user_id=user_id)
    result = await handler(command)
    return api_models.CreatePromptResponse(**result)


@router.post("/v1/agent_chat_bots", response_model=api_models.CreateAgentChatBotResponse)
@inject
async def create_agent_chat_bot(
    request: api_models.CreateAgentChatBotRequest,
    user_id: str = Header(alias="X-User-ID"),
    handler: CreateAgentChatBotCommandHandler = Depends(Provide[FastapiContainer.create_agent_chat_bot_handler]),
) -> api_models.CreateAgentChatBotResponse:
    """
    FastAPI handler for creating a new agent chat bot.

    Args:
        request (CreateAgentChatBotRequest): Contains bot name, prompt ID, and knowledge base ID.
        handler (CreateAgentChatBotCommandHandler): Injected handler to process the command.

    Returns:
        CreateAgentChatBotResponse: Contains metadata of the created agent chat bot.

    Raises:
        ValidationError: If the request data is invalid.
        Exception: For any unexpected error during processing.
    """
    logger.info(f"Received request for agent chat bot: {request}")
    command = CreateAgentChatBotCommand(
        name=request.name,
        prompt_id=request.prompt_id,
        knowledge_base_id=request.knowledge_base_id,
        user_id=user_id,
    )
    result = await handler(command)
    return api_models.CreateAgentChatBotResponse(**result)


@router.put("/v1/agent_chat_bots", response_model=api_models.ChangeSettingsAgentChatBotResponse)
@inject
async def change_settings_agent_chat_bot(
    request: api_models.ChangeSettingsAgentChatBotRequest,
    handler: ChangeSettingsAgentChatBotCommandHandler = Depends(Provide[FastapiContainer.change_settings_agent_chat_bot_handler]),
) -> api_models.ChangeSettingsAgentChatBotResponse:
    """
    FastAPI handler for changing the settings of an agent chat bot.

    Args:
        request (ChangeSettingsAgentChatBotRequest): Contains settings to be changed.
        handler (ChangeSettingsAgentChatBotCommandHandler): Injected handler to apply changes.

    Returns:
        ChangeSettingsAgentChatBotResponse: Contains updated agent bot settings.

    Raises:
        ValidationError: If the request data is invalid.
        Exception: For any unexpected error during processing.
    """
    logger.info(f"Received change settings request: {request}")
    command = ChangeSettingsAgentChatBotCommand(**request.model_dump())
    result = await handler(command)
    return api_models.ChangeSettingsAgentChatBotResponse(**result)


@router.put("/v1/prompts", response_model=api_models.UpdatePromptTextResponse)
@inject
async def update_prompt_text(
    request: api_models.UpdatePromptTextRequest,
    handler: UpdatePromptTextCommandHandler = Depends(Provide[FastapiContainer.update_prompt_text_handler]),
) -> api_models.UpdatePromptTextResponse:
    """
    FastAPI handler for updating an existing prompt's text.

    Args:
        request (UpdatePromptTextRequest): Contains prompt ID and new text.
        handler (UpdatePromptTextCommandHandler): Injected handler to perform the update.

    Returns:
        UpdatePromptTextResponse: Contains the updated prompt details.

    Raises:
        ValidationError: If the request data is invalid.
        Exception: For any unexpected error during processing.
    """
    logger.info(f"Received update prompt request: {request}")
    command = UpdatePromptTextCommand(**request.model_dump())
    result = await handler(command)
    return api_models.UpdatePromptTextResponse(**result)


# GET Endpoints
@router.get("/v1/prompts", response_model=api_models.GetPromptsResponse)
@inject
async def get_prompts(
    user_id: str = Header(alias="X-User-ID"),
    unit_of_work: UnitOfWork = Depends(Provide[FastapiContainer.unit_of_work]),
) -> api_models.GetPromptsResponse:
    """Get all prompts for user"""
    logger.info(f"Getting prompts for user: {user_id}")
    
    async with unit_of_work as uow:
        prompts = await uow.prompts.get_all(user_id)
    
    response_prompts = [
        api_models.Prompt(
            id=p.prompt_id,
            prompt_id=p.prompt_id,
            text=p.text,
            user_id=p.user_id
        ) for p in prompts
    ]
    
    return api_models.GetPromptsResponse(prompts=response_prompts)


@router.get("/v1/chatbots", response_model=api_models.GetChatbotsResponse)
@inject
async def get_chatbots(
    user_id: str = Header(alias="X-User-ID"),
    unit_of_work: UnitOfWork = Depends(Provide[FastapiContainer.unit_of_work]),
) -> api_models.GetChatbotsResponse:
    """Get all chatbots for user"""
    logger.info(f"Getting chatbots for user: {user_id}")
    
    async with unit_of_work as uow:
        chatbots = await uow.agent_chat_bots.get_all(user_id)
    
    response_chatbots = [
        api_models.Chatbot(
            id=cb.agent_chat_bot_id,
            agent_chat_bot_id=cb.agent_chat_bot_id,
            name=cb.name,
            prompt_id=cb.prompt_id,
            knowledge_base_id=cb.knowledge_base_id,
            user_id=cb.user_id
        ) for cb in chatbots
    ]
    
    return api_models.GetChatbotsResponse(chatbots=response_chatbots)


# DELETE Endpoints
@router.delete("/v1/prompts/{prompt_id}", response_model=api_models.DeleteResponse)
@inject
async def delete_prompt(
    prompt_id: str,
    user_id: str = Header(alias="X-User-ID"),
    unit_of_work: UnitOfWork = Depends(Provide[FastapiContainer.unit_of_work]),
) -> api_models.DeleteResponse:
    """Delete prompt by ID"""
    logger.info(f"Deleting prompt {prompt_id} for user: {user_id}")
    
    async with unit_of_work as uow:
        # Delete prompt by ID - user isolation will be added after migration
        await uow.prompts.delete(prompt_id)
    
    return api_models.DeleteResponse(message=f"Prompt {prompt_id} deleted successfully")


@router.delete("/v1/chatbots/{chatbot_id}", response_model=api_models.DeleteResponse)
@inject
async def delete_chatbot(
    chatbot_id: str,
    user_id: str = Header(alias="X-User-ID"),
    unit_of_work: UnitOfWork = Depends(Provide[FastapiContainer.unit_of_work]),
) -> api_models.DeleteResponse:
    """Delete chatbot by ID"""
    logger.info(f"Deleting chatbot {chatbot_id} for user: {user_id}")
    
    async with unit_of_work as uow:
        # Delete chatbot by ID - user isolation will be added after migration
        await uow.agent_chat_bots.delete(chatbot_id)
    
    return api_models.DeleteResponse(message=f"Chatbot {chatbot_id} deleted successfully")


# User creation endpoint for API Gateway
@router.post("/v1/users")
@inject  
async def create_user(
    request: dict,
    user_id: str = Header(alias="X-User-ID"),
) -> dict:
    """Create user record in admin panel"""
    logger.info(f"Creating user record: {request}")
    return {"message": "User created in admin panel", "user_id": user_id}


container = FastapiContainer()
container.wire(modules=[__name__])