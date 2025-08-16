
from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Optional
from dependency_injector.wiring import inject, Provide

router = APIRouter()

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

@router.get("/v1/prompts")
@inject
async def get_user_prompts(
    x_user_id: str = Header(..., alias="X-User-ID"),
    unit_of_work = Depends(Provide["unit_of_work"])
):
    async with unit_of_work as uow:
        prompts = await uow.prompts.get_by_user_id(x_user_id)
        return {"prompts": prompts}

@router.get("/v1/chatbots")
@inject
async def get_user_chatbots(
    x_user_id: str = Header(..., alias="X-User-ID"),
    unit_of_work = Depends(Provide["unit_of_work"])
):
    async with unit_of_work as uow:
        chatbots = await uow.chatbots.get_by_user_id(x_user_id)
        return {"chatbots": chatbots}


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


router = fastapi.APIRouter()

@router.post("/v1/prompts", response_model=api_models.CreatePromptResponse)
@inject
async def create_prompt(
    request: api_models.CreatePromptRequest,
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
    command = CreatePromptCommand(text=request.text)
    result = await handler(command)
    return api_models.CreatePromptResponse(**result)


@router.post("/v1/agent_chat_bots", response_model=api_models.CreateAgentChatBotResponse)
@inject
async def create_agent_chat_bot(
    request: api_models.CreateAgentChatBotRequest,
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



container = FastapiContainer()
container.wire(modules=[__name__])