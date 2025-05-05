from opensearchpy import AsyncOpenSearch

from src.application.models.vectorized_knowledge import Resource, VectorizedKnowledge
from src.application.ports.unit_of_work import VectorizedKnowledgeRepository


class OpensearchVectorizedKnowledgeRepository(VectorizedKnowledgeRepository):
    """
    Repository implementation for managing vectorized knowledge using OpenSearch.

    Inherits from VectorizedKnowledgeRepository and provides methods to interact with OpenSearch for
    storing and retrieving vectorized knowledge data.

    Attributes:
        _client (AsyncOpenSearch): The OpenSearch client for interacting with OpenSearch service.
        _index (str): The OpenSearch index name for storing vectorized knowledge resources.
    """

    def __init__(self, client: AsyncOpenSearch, knn_parameter: int):
        """
        Initializes the OpensearchVectorizedKnowledgeRepository with an OpenSearch client.

        Args:
            client (AsyncOpenSearch): The OpenSearch client used for interacting with OpenSearch service.
        """
        self._client = client
        self._k = knn_parameter
        self._index = "vectorized_knowledge_resource"  # The OpenSearch index for vectorized knowledge resources

    async def get(self, knowledge_base_id: str, resource_ids: list[str]):
        """
        Retrieves vectorized knowledge resources from OpenSearch based on resource IDs.

        Args:
            knowledge_base_id (str): The ID of the knowledge base.
            resource_ids (list[str]): The list of resource IDs to fetch.

        Returns:
            VectorizedKnowledge: The vectorized knowledge containing resources that match the query.
        """
        query = {
            "query": {
                "bool": {
                    "filter": [
                        {"terms": {"resource_id": resource_ids}},
                    ]
                }
            }
        }
        response = await self._client.search(index=self._index, body=query)
        resources = [
            Resource(
                resource_id=hit["_source"]["resource_id"],
                vector=hit["_source"]["vector"],
                content=hit["_source"]["content"],
            )
            for hit in response["hits"]["hits"]
        ]
        return VectorizedKnowledge(
            knowledge_base_id=knowledge_base_id, resources=resources
        )  # Return the vectorized knowledge with the resources

    async def get_knn(
        self, knowledge_base_id: str, resource_ids: list[str], vectorized_query: list
    ):
        """
        Retrieves the K nearest neighbors (KNN) for vectorized knowledge resources using a vectorized query.

        Args:
            knowledge_base_id (str): The ID of the knowledge base.
            resource_ids (list[str]): The list of resource IDs to filter by.
            vectorized_query (list): The vectorized query to find similar resources.

        Returns:
            VectorizedKnowledge: The vectorized knowledge containing the K nearest neighbors.
        """
        if not resource_ids:
            return VectorizedKnowledge(
                knowledge_base_id=knowledge_base_id, resources=[]
            )

        query = {
            "size": self._k,  # Limit the number of results to K
            "query": {
                "bool": {
                    "must": [
                        {
                            "knn": {
                                "vector": {
                                    "vector": vectorized_query,  # Use vectorized query for KNN search
                                    "k": self._k,  # Number of neighbors to return
                                }
                            }
                        }
                    ],
                    "filter": [
                        {
                            "terms": {"resource_id": resource_ids}
                        },  # Filter by resource IDs
                    ],
                }
            },
        }

        response = await self._client.search(
            index=self._index, body=query
        )  # Perform the KNN search in OpenSearch
        knn_resources = [
            Resource(
                resource_id=hit["_source"][
                    "resource_id"
                ],  # Extract KNN resources from the response
                vector=hit["_source"]["vector"],
                content=hit["_source"]["content"],
            )
            for hit in response["hits"]["hits"]
        ]

        return VectorizedKnowledge(
            knowledge_base_id=knowledge_base_id, resources=knn_resources
        )  # Return the vectorized knowledge with KNN resources
