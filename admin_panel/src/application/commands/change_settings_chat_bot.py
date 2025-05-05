from dataclasses import dataclass

from src.application.commands.base import BaseCommand


@dataclass
class ChangeSettingsAgentChatBotCommand(BaseCommand):
    agent_chat_bot_id: str
    knowledge_base_id: str | None = None
    prompt_id: str | None = None
