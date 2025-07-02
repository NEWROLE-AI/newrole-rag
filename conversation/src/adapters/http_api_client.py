import json

import aiohttp
from aiohttp import ClientError
from aiohttp.web_exceptions import HTTPError
from aws_lambda_powertools import Logger

from src.application.ports.api_client import (
    SourceManagementApiClient,
    VectorizerApiClient,
)


logger = Logger("http_api_client")


class HttpSourceManagementApiClient(SourceManagementApiClient):
    """
    HTTP client for interacting with the Source Management API to fetch resources based on knowledge base IDs.

    Attributes:
        _session (aiohttp.ClientSession): The HTTP session used for making requests.
        _base_url (str): The base URL of the Source Management API.
    """

    def __init__(self, session: aiohttp.ClientSession, source_management_url: str):
        """
        Initializes the HTTP client with the session and the base URL for the Source Management API.

        Args:
            session (aiohttp.ClientSession): The session for making HTTP requests.
            source_management_url (str): The base URL of the Source Management API.
        """
        self._session = session
        self._base_url = source_management_url

    async def get_resource_info_by_knowledge_base_id(
        self, knowledge_base_id: str
    ) -> list[str]:
        """
        Fetches the resource IDs associated with a knowledge base ID from the Source Management API.

        Args:
            knowledge_base_id (str): The ID of the knowledge base.

        Returns:
            list[str]: A list of resource IDs associated with the knowledge base.
        """
        url = f"{self._base_url}/api/v1/{knowledge_base_id}/resources"
        logger.info(
            f"HttpSourceManagementApiClient: Fetching resources ids with ID={knowledge_base_id}"
        )
        try:
            async with self._session.get(
                url, params={"knowledge_base_id": knowledge_base_id}
            ) as response:
                if response.status != 200:
                    logger.error(
                        f"Error fetching resources ids by knowledge_base_id data for ID={knowledge_base_id}: HTTP {response.status}"
                    )
                    raise HTTPError()
                resource_info = await response.json()
            logger.info(
                f"HttpSourceManagementApiClient: Successfully fetched resource ids data for ID={knowledge_base_id}"
            )
            return resource_info
        except ClientError as e:
            logger.error(
                f"HTTP ClientError while fetching resource ids with ID={knowledge_base_id}: {str(e)}"
            )
            raise


    async def get_data(self, request_body: dict) -> dict:
        url = f"{self._base_url}/api/v1/data/retrieve"
        logger.info(
            f"HttpSourceManagementApiClient: Get resource data"
        )
        try:
            async with self._session.post(
                    url, json=request_body
            ) as response:
                if response.status != 200:
                    logger.error(
                        f"Error fetching resources data: HTTP {response.status}"
                    )
                    raise HTTPError()
                resource_data = await response.json()
            logger.info(
                f"HttpSourceManagementApiClient: Successfully fetched resource data"
            )
            return resource_data
        except ClientError as e:
            logger.error(
                f"HTTP ClientError while fetching resource data: {str(e)}"
            )
            raise


class HttpVectorizerApiClient(VectorizerApiClient):
    """
    HTTP client for interacting with the Vectorizer API to convert text into vectorized representations.

    Attributes:
        _session (aiohttp.ClientSession): The HTTP session used for making requests.
        _base_url (str): The base URL of the Vectorizer API.
    """

    def __init__(self, session: aiohttp.ClientSession, vectorize_service_url: str):
        """
        Initializes the HTTP client with the session and the base URL for the Vectorizer API.

        Args:
            session (aiohttp.ClientSession): The session for making HTTP requests.
            vectorize_service_url (str): The base URL of the Vectorizer API.
        """
        self._session = session
        self._base_url = vectorize_service_url

    async def vectorize_text(self, text: str) -> list:
        """
        Vectorizes the provided text using the Vectorizer API.

        Args:
            text (str): The text to be vectorized.

        Returns:
            list: The vectorized representation of the text.
        """
        url = f"{self._base_url}/api/v1/vectorize_text"
        logger.info(
            "HttpVectorizerApiClient: Vectorizing text", extra={"vectorize_text": text}
        )
        try:
            async with self._session.post(url, json={"text": text}) as response:
                if response.status != 200:
                    logger.error(f"Error vectorizing text: {response.status}")
                    raise HTTPError()
                vectorized_text = await response.json()
                logger.info("HttpVectorizerApiClient: Successfully vectorized text")
            return vectorized_text.get("vectorized_text", [])
        except ClientError as e:
            logger.error(
                f"HTTP ClientError while vectorizing text: {response.status}: {str(e)}"
            )
            raise
