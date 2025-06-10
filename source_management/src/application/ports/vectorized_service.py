from abc import ABC, abstractmethod

from src.application.models.vectorized_resource import VectorizedKnowledgeResource


class VectorizedService(ABC):
    
    @abstractmethod
    async def get_vector(self, resource: VectorizedKnowledgeResource) -> list:
        raise NotImplementedError