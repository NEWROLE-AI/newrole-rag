from dataclasses import dataclass

from src.application.commands.base import BaseCommand


@dataclass
class CreateKnowledgeBaseCommand(BaseCommand):
    """
    Command for creating a new Knowledge Base.

    This command carries the necessary data for creating a knowledge base.

    Attributes:
        knowledge_base_name (str): The name of the knowledge base.
    """

    knowledge_base_name: str
