from logging import Logger

from dependency_injector.wiring import inject, Provide, Closing

from src.application.command_handlers.change_settings_chat_bot import (
    ChangeSettingsAgentChatBotCommandHandler,
)
from src.application.command_handlers.create_agent_chat_bot import (
    CreateAgentChatBotCommandHandler,
)
from src.application.command_handlers.create_prompt import CreatePromptCommandHandler
from src.application.command_handlers.update_prompt_text import UpdatePromptTextCommandHandler
from src.application.commands.change_settings_chat_bot import (
    ChangeSettingsAgentChatBotCommand,
)
from src.application.commands.create_agent_chat_bot import CreateAgentChatBotCommand
from src.application.commands.create_prompt import CreatePromptCommand
from src.application.commands.update_prompt_text import UpdatePromptTextCommand
from src.entrypoints.api.middleware.utils import lambda_handler_decorator
from src.entrypoints.api.models import api_models
from src.entrypoints.api.ioc import Container

logger = Logger("handlers")


@lambda_handler_decorator(api_models.CreatePromptRequest)
@inject
async def create_prompt(
    request: api_models.CreatePromptRequest,
    handler: CreatePromptCommandHandler = Closing[
        Provide[Container.create_prompt_handler]
    ],
) -> api_models.CreatePromptResponse:
    """
    Handles requests to create a new prompt. The function processes a CreatePromptRequest
    using a CreatePromptCommandHandler and returns a CreatePromptResponse.

    Args:
        request (api_models.CreatePromptRequest): The incoming prompt creation request.
        handler (CreatePromptCommandHandler): The command handler to process the request.

    Returns:
        api_models.CreatePromptResponse: The response containing the newly created prompt's data.
    """
    logger.info(f"Received request for prompt: {request}")
    # Create a command object from the request data
    command = CreatePromptCommand(
        text=request.text,
    )
    logger.info(f"Created command: {command}")

    # Log handler instance and execute
    logger.info(f"Handler instance before execution: {handler}")
    result = await handler(command)
    logger.info("Handler execution completed")

    # Create and return response
    response = api_models.CreatePromptResponse(**result)
    logger.info(f"Returning response: {response}")
    return response


@lambda_handler_decorator(api_models.CreateAgentChatBotRequest)
@inject
async def create_agent_chat_bot(
    request: api_models.CreateAgentChatBotRequest,
    handler: CreateAgentChatBotCommandHandler = Closing[
        Provide[Container.create_agent_chat_bot_handler]
    ],
) -> api_models.CreateAgentChatBotResponse:
    """
    Handles requests to create a new agent chat bot. Processes a CreateAgentChatBotRequest
    using a CreateAgentChatBotCommandHandler and returns a CreateAgentChatBotResponse.

    Args:
        request (api_models.CreateAgentChatBotRequest): The incoming chat bot creation request.
        handler (CreateAgentChatBotCommandHandler): The command handler to process the request.

    Returns:
        api_models.CreateAgentChatBotResponse: The response containing the newly created chat bot's data.
    """
    logger.info(f"Received request for agent chat bot: {request}")
    # Create command from request data
    command = CreateAgentChatBotCommand(
        name=request.name,
        prompt_id=request.prompt_id,
        knowledge_base_id=request.knowledge_base_id,
    )
    logger.info(f"Created command: {command}")

    # Execute handler and create response
    logger.info(f"Handler instance before execution: {handler}")
    result = await handler(command)
    logger.info("Handler execution completed")

    response = api_models.CreateAgentChatBotResponse(**result)
    logger.info(f"Returning response: {response}")
    return response


@lambda_handler_decorator(api_models.ChangeSettingsAgentChatBotRequest)
@inject
async def change_settings_agent_chat_bot(
    request: api_models.ChangeSettingsAgentChatBotRequest,
    handler: ChangeSettingsAgentChatBotCommandHandler = Closing[
        Provide[Container.change_settings_agent_chat_bot_handler]
    ],
) -> api_models.ChangeSettingsAgentChatBotResponse:
    """
    Handles requests to change settings of an existing agent chat bot. Processes a
    ChangeSettingsAgentChatBotRequest and returns a ChangeSettingsAgentChatBotResponse.

    Args:
        request (api_models.ChangeSettingsAgentChatBotRequest): The settings change request.
        handler (ChangeSettingsAgentChatBotCommandHandler): The command handler to process the request.

    Returns:
        api_models.ChangeSettingsAgentChatBotResponse: The response containing the updated settings.
    """
    logger.info(f"Received request for agent chat bot: {request}")
    # Create command from request
    command = ChangeSettingsAgentChatBotCommand(**request.model_dump())
    logger.info(f"Created command: {command}")

    # Execute handler
    logger.info(f"Handler instance before execution: {handler}")
    result = await handler(command)
    logger.info("Handler execution completed")

    response = api_models.ChangeSettingsAgentChatBotResponse(**result)
    logger.info(f"Returning response: {response}")
    return response


@lambda_handler_decorator(api_models.UpdatePromptTextRequest)
@inject
async def update_prompt_text(
    request: api_models.UpdatePromptTextRequest,
    handler: UpdatePromptTextCommandHandler = Closing[
        Provide[Container.update_prompt_text_handler]
    ],
) -> api_models.UpdatePromptTextResponse:
    """
    Handles requests to update text of an existing prompt. Processes a
    UpdatePromptTextRequest and returns a UpdatePromptTextResponse.

    Args:
        request (api_models.UpdatePromptTextRequest): The settings change request.
        handler (UpdatePromptTextCommandHandler): The command handler to process the request.

    Returns:
        api_models.UpdatePromptTextResponse: The response containing the updated settings.
    """
    logger.info(f"Received request for update text prompt: {request}")
    # Create command from request
    command = UpdatePromptTextCommand(**request.model_dump())
    logger.info(f"Created command: {command}")

    # Execute handler
    logger.info(f"Handler instance before execution: {handler}")
    result = await handler(command)
    logger.info("Handler execution completed")

    response = api_models.UpdatePromptTextResponse()
    logger.info(f"Returning response: {response}")
    return response


container = Container()
container.wire(modules=[__name__])
