from dataclasses import dataclass

from src.application.commands.base import BaseCommand


@dataclass
class CreateAgentChatBotCommand(BaseCommand):
    name: str
    prompt_id: str | None = None
    knowledge_base_id: str | None = None
