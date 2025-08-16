from abc import ABC, abstractmethod

import aiohttp
from aiohttp import ClientError
from aiohttp.web_exceptions import HTTPError
from aws_lambda_powertools import Logger

from src.application.models.vectorized_resource import VectorizedKnowledgeResource
from src.application.ports.vectorized_service import VectorizedService

logger = Logger("sql_unit_of_work")

class HttpVectorizedService(VectorizedService):

    def __init__(self, base_url: str, session: aiohttp.ClientSession):
        self._base_url = base_url
        self._session = session

    async def get_vector(self, resource: VectorizedKnowledgeResource) -> list:
        url = f"{self._base_url}/api/v1/vectorization"
        try:
            async with self._session.post(
                    url,
                    json={
                        "content": resource.content,
                        "resource_id": resource.resource_id,
                    },
            ) as response:
                if response.status != 200:
                    logger.error(
                        f"Error processing static file from Vectorization API: {response.status}"
                    )
                    raise HTTPError()
                status = await response.json()
                logger.info(
                    f"HttpHandlerResourceApiClient: Static file processing from Vectorization API"
                )
                return status
        except ClientError as e:
            logger.error(
                f"HTTP ClientError while processing static file from Vectorization API: {e}"
            )
            raise