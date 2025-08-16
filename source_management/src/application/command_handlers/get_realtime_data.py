import asyncio
from dataclasses import asdict
from typing import Callable

from aws_lambda_powertools import Logger
from click import command

from src.application.command_handlers.base import BaseCommandHandler
from src.application.commands.get_realtime_data import GetRealtimeDataCommand, RealtimeResourceType, DatabaseProperties
from src.application.models import realtime_resource
from src.application.models.realtime_resource import DbType
from src.application.ports.database_manager import DatabaseManager
from src.application.ports.realtime_api_service import RealtimeApiService
from src.application.ports.realtime_database_service import RealtimeDatabaseService
from src.application.ports.unit_of_work import UnitOfWork

logger = Logger(service="get_realtime_data")


class GetRealtimeDataCommandHandler(BaseCommandHandler):

    def __init__(self,
                 unit_of_work: UnitOfWork,
                 api_service: RealtimeApiService,
                 db_handlers: dict[DbType, RealtimeDatabaseService],
                 database_manager: DatabaseManager
    ):
        self._uow = unit_of_work
        self._api_service = api_service
        self._db_handlers = db_handlers
        self._database_manager = database_manager

    async def __call__(self, command: GetRealtimeDataCommand):
        logger.info("Getting realtime data")
        logger.info(f"Realtime resource: {command.realtime_resource}")
        task_list = []

        for resource in command.realtime_resource:
            if resource.resource_type == RealtimeResourceType.DATABASE:
                task_list.append(self._get_database_data(resource.resource_id, resource.knowledge_base_id, resource.additional_properties))
            if resource.resource_type == RealtimeResourceType.REST_API:
                task_list.append(self._get_rest_api_data(resource.resource_id, resource.additional_properties))
        logger.info(f"Getting realtime data: {len(task_list)} tasks")
        return await asyncio.gather(*task_list)


    async def _get_database_data(self, resource_id: str, knowledge_base_id: str, additional_properties: DatabaseProperties):
        try:
            logger.info(f"Getting database data: {resource_id}")
            await self._database_manager.check_query(additional_properties.query)
            async with self._uow as uow:
                connection_params = await uow.realtime_databases.get_connection_params_by_id(resource_id, knowledge_base_id)
                db_type = DbType((await uow.realtime_resources.get_by_id(resource_id)).extra.db_type)
            data = await self._db_handlers[db_type].execute_query(additional_properties.query, connection_params.get("connection_params", dict()))
            logger.info(f"Database data of resource {resource_id}: {data}")
            return {resource_id: data}

        except Exception as e:
            logger.error(f"Error getting database data: {e}")
            return {resource_id: f"Error getting database data: {e}"}


    async def _get_rest_api_data(self, resource_id, additional_properties):
        try:
            logger.info(f"Getting rest api data: {resource_id}")
            async with self._uow as uow:
                url = (await uow.realtime_resources.get_by_id(resource_id)).extra.url

            rest_api = realtime_resource.RestApi(
                url=url,
                header=additional_properties.header,
                query_params=additional_properties.query_params,
                payload=additional_properties.payload,
                method=additional_properties.method.value,
                placeholders=additional_properties.placeholders
            )
            logger.info(f"Rest api data of resource {resource_id}: {rest_api}")
            return {resource_id: await self._api_service.get_data(rest_api)}

        except Exception as e:
            logger.error(f"Error getting rest api data: {e}")
            return {resource_id: f"Error getting database data: {e}"}