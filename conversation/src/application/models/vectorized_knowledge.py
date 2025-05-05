from dataclasses import dataclass
from typing import Any


@dataclass
class Resource:
    """
    Represents a resource that is part of the knowledge base.

    Attributes:
        resource_id (str): The unique ID of the resource.
        vector (list[float]): The vector representation of the resource content.
        content (str): The content of the resource.
    """

    resource_id: str
    vector: list[float]
    content: str


@dataclass
class VectorizedKnowledge:
    """
    Represents the vectorized knowledge base.

    Attributes:
        knowledge_base_id (str): The ID of the knowledge base.
        resources (list[Resource]): The list of resources in the knowledge base.
    """

    knowledge_base_id: str
    resources: list[Resource]
