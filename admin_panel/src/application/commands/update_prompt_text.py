from dataclasses import dataclass

from src.application.commands.base import BaseCommand


@dataclass
class UpdatePromptTextCommand(BaseCommand):
    prompt_id: str
    text: str = ""
