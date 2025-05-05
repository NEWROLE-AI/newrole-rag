from abc import ABC, abstractmethod


class StorageManager(ABC):
    """
    Abstract base class for storage managers.

    Defines the contract for generating presigned URLs for resources.
    """

    @abstractmethod
    async def generate_presigned_url(
        self, knowledge_base_name: str, resource_name: str, file_type: str | None
    ) -> str:
        """
        Abstract method to generate a presigned URL for a resource.

        Args:
            knowledge_base_name (str): The knowledge base's name.
            resource_name (str): The resource's name.
            file_type (str | None): The file type (optional).

        Returns:
            str: The presigned URL for uploading or accessing the resource.
        """
        raise NotImplementedError
