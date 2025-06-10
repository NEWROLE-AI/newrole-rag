from abc import ABC, abstractmethod

from opensearchpy import AsyncOpenSearch

from src.application.models.vectorized_resource import VectorizedKnowledge


class VectorizedKnowledgeService(ABC):

    @abstractmethod
    async def get_knn(
        self, knowledge_base_id: str, resource_ids: list[str], vectorized_query: list
    ) -> VectorizedKnowledge:
        raise NotImplementedError
