from dataclasses import dataclass

from src.application.commands.base import BaseCommand

@dataclass
class VectorizationResource:
    resource_id: str
    knowledge_base_id: str
    input_data: str | None = None


@dataclass
class GetVectorizedDataCommand(BaseCommand):
    vectorization_resources: list[VectorizationResource]


