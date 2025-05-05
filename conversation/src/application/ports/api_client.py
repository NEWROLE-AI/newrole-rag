from abc import ABC, abstractmethod


class SourceManagementApiClient(ABC):
    """
    Interface for the source management API client.

    Methods:
        get_resource_ids_by_knowledge_base_id: Fetches resource IDs for a given knowledge base.
    """

    @abstractmethod
    async def get_resource_ids_by_knowledge_base_id(
        self, knowledge_base_id: str
    ) -> list[str]:
        raise NotImplementedError


class VectorizerApiClient(ABC):
    """
    Interface for the vectorizer API client.

    Methods:
        vectorize_text: Converts a text message into a vector representation.
    """

    @abstractmethod
    async def vectorize_text(self, text: str) -> list:
        raise NotImplementedError
