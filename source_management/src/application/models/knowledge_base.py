from dataclasses import dataclass, field

from src.application.models.resource import Resource


@dataclass
class KnowledgeBase:
    """
    Represents a Knowledge Base.

    A KnowledgeBase holds multiple resources and has a unique identifier.

    Attributes:
        knowledge_base_id (str): The unique identifier for the knowledge base.
        name (str): The name of the knowledge base.
        resources (list[Resource]): A list of resources associated with the knowledge base.
    """

    knowledge_base_id: str
    name: str
    resources: list[Resource] = field(default_factory=list)
