from pydantic import BaseModel


class CreatePromptRequest(BaseModel):
    text: str


class CreatePromptResponse(BaseModel):
    prompt_id: str


class CreateAgentChatBotRequest(BaseModel):
    name: str
    knowledge_base_id: str | None = None
    prompt_id: str | None = None


class CreateAgentChatBotResponse(BaseModel):
    agent_chat_bot_id: str


class ChangeSettingsAgentChatBotRequest(BaseModel):
    agent_chat_bot_id: str
    knowledge_base_id: str | None = None
    prompt_id: str | None = None


class UpdatePromptTextRequest(BaseModel):
    prompt_id: str
    text: str = ""


class UpdatePromptTextResponse(BaseModel):
    message: str = "Success"


class ChangeSettingsAgentChatBotResponse(BaseModel):
    agent_chat_bot_id: str


# GET Response Models
class Prompt(BaseModel):
    id: str
    prompt_id: str
    text: str


class GetPromptsResponse(BaseModel):
    prompts: list[Prompt]


class Chatbot(BaseModel):
    id: str
    agent_chat_bot_id: str
    name: str
    prompt_id: str | None = None
    knowledge_base_id: str | None = None
    user_id: str


class GetChatbotsResponse(BaseModel):
    chatbots: list[Chatbot]


class DeleteResponse(BaseModel):
    message: str = "Deleted successfully"
