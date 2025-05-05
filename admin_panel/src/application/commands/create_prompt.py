from dataclasses import dataclass

from src.application.commands.base import BaseCommand


@dataclass
class CreatePromptCommand(BaseCommand):
    text: str
