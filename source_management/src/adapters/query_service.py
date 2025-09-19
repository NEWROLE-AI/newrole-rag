import json
import motor.motor_asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from boto3_type_annotations.dynamodb import Client
from boto3_type_annotations.secretsmanager import Client as SecretManagerClient


class DynamoQueryService:
    """
    A service class for querying resources based on knowledge base IDs.

    The QueryService uses SQLAlchemy's AsyncSession to interact with the database.
    It provides methods for fetching resource IDs associated with a knowledge base ID.
    """

    def __init__(
        self,
        sql_session: AsyncSession,
        dynamo_client: Client,
        secrets_manager_client: SecretManagerClient,
    ):
        """
        Initializes the QueryService with a given SQLAlchemy AsyncSession.

        Args:
            sql_session (AsyncSession): The SQLAlchemy AsyncSession instance to interact with the database.
            dynamo_client (Client): The DynamoDB Client instance to interact with the database.
            secrets_manager_client (SecretManagerClient): The SecretManagerClient instance to interact with the database.
        """
        self._sql_session = sql_session
        self._dynamo_client = dynamo_client
        self._slack_channels = self._dynamo_client.Table(
            "slack-channel-info-resources-dev"
        )
        self._secrets_manager_client = secrets_manager_client

    async def get_resource_ids_by_knowledge_base_id(
        self, knowledge_base_id: str, user_id: str
    ) -> dict[str, list[str]]:
        """
        Fetches a list of resource IDs associated with a specific knowledge base ID for the given user.

        Args:
            knowledge_base_id (str): The ID of the knowledge base.
            user_id (str): The ID of the user to filter results.

        Returns:
            dict: A dictionary with a key "resource_ids" containing a list of resource IDs.
        """
        query = text(
            """
                SELECT r.resource_id
                FROM resources r
                WHERE r.knowledge_base_id = (
                    SELECT kb.id
                    FROM knowledge_bases kb
                    WHERE kb.knowledge_base_id = :knowledge_base_id
                    AND kb.user_id = :user_id
                )
            """
        )
        # Execute the query asynchronously and fetch results
        result = await self._sql_session.execute(
            query, {"knowledge_base_id": knowledge_base_id, "user_id": user_id}
        )
        # Extract resource IDs from the query result
        resource_ids = [row[0] for row in result.fetchall()]
        return {"resource_ids": resource_ids}

    async def get_all_resources(self, user_id: str) -> list[dict]:
        """
        Fetches all resources associated with knowledge bases for the given user.

        Args:
            user_id (str): The ID of the user to filter results.

        Returns:
            list: A list with dictionary with a key "knowledge_base_id" containing a list of resources.
        """
        query = text(
            """
            SELECT
                kb.knowledge_base_id,
                r.resource_id,
                r.type,
                r.extension,
                r.google_drive_url,
                r.dynamodb_table_name
            FROM knowledge_bases kb
            LEFT JOIN resources r ON kb.id = r.knowledge_base_id
            WHERE kb.user_id = :user_id
            ORDER BY kb.knowledge_base_id
            """
        )

        result = await self._sql_session.execute(query)
        rows = result.fetchall()

        resources_by_kb = {}
        for row in rows:
            (
                kb_id,
                resource_id,
                resource_type,
                extension,
                google_drive_url,
                dynamodb_table_name,
            ) = row
            if kb_id not in resources_by_kb:
                resources_by_kb[kb_id] = {"knowledge_base_id": kb_id, "resources": []}

            if resource_id and resource_type:  # Check if resource exists
                resource_info = {
                    "resource_id": resource_id,
                    "resource_type": resource_type,
                }
                if resource_type == "SLACK_CHANNEL":
                    try:
                        response = self._slack_channels.get_item(
                            Key={"resource_id": resource_id}
                        )
                        if "Item" in response:
                            channel_info = response["Item"]
                            resource_info.update(
                                {
                                    "channel_id": channel_info.get("channel_id"),
                                    "messages": channel_info.get("messages", []),
                                }
                            )
                    except Exception as e:
                        raise
                elif resource_type == "STATIC_FILE":
                    resource_info.update({"key": f"{kb_id}/{resource_id}.{row[3]}"})
                elif resource_type == "DATABASE":
                    key = f"database_info/{kb_id}/{resource_id}"
                    response = self._secrets_manager_client.get_secret_value(key)
                    secret_data = json.loads(response["SecretString"])
                    resource_info.update(
                        {
                            "query": secret_data.get("query"),
                            "connection_params": secret_data.get("connection_params"),
                        }
                    )
                elif resource_type == "GOOGLE_DRIVE":
                    resource_info.update({"google_drive_url": google_drive_url})
                elif resource_type == "DYNAMODB":
                    resource_info.update({"dynamodb_table_name": dynamodb_table_name})

                resources_by_kb[kb_id]["resources"].append(resource_info)
        return list(resources_by_kb.values())


import motor.motor_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import List, Dict
import json


class MongoQueryService:

    def __init__(
            self,
            mongo_client: motor.motor_asyncio.AsyncIOMotorClient,
            database_name: str = "source-managment"
    ):

        self._mongo_client = mongo_client
        self._mongo_db = self._mongo_client[database_name]
        self._resources_collection = self._mongo_db.get_collection("resources")

    async def get_resource_ids_by_knowledge_base_id(
            self, knowledge_base_id: str
    ) -> Dict[str, List[str]]:
        """
        Получить resource_ids по knowledge_base_id из MongoDB.
        """
        resource_ids = await self._resources_collection.find(
            {"knowledge_base_id": knowledge_base_id},
            {"_id": 0, "resource_id": 1},
        ).to_list()
        return {"resource_ids": [row['resource_id'] for row in resource_ids]}

    async def get_all_resources(self, knowledge_base_ids: list[str]) -> List[dict]:
        cursor = self._resources_collection.find(
            {"knowledge_base_id": {"$in": knowledge_base_ids}}
        )

        resources = []

        async for resource_doc in cursor:
            resource_info = {
                "resource_id": resource_doc.get("resource_id"),
                "type": resource_doc.get("type"),
                "extra": resource_doc.get("extra", {}),
                "knowledge_base_id": resource_doc.get("knowledge_base_id")
            }
            resources.append(resource_info)

        return resources

