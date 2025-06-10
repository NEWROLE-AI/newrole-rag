import asyncio

from aws_lambda_powertools import Logger
from click import command

from src.application.command_handlers.base import BaseCommandHandler
from src.application.commands.get_vectorized_data import GetVectorizedDataCommand
from src.application.models.vectorized_resource import VectorizedKnowledgeResource
from src.application.ports.opensearch_service import VectorizedKnowledgeService
from src.application.ports.unit_of_work import UnitOfWork
from src.application.ports.vectorized_service import VectorizedService
from src.entrypoints.api.models.api_models import VectorizationResource

logger = Logger(service="get_vectorized_data")


class GetVectorizedDataCommandHandler(BaseCommandHandler):
    def __init__(
            self,
            unit_of_work: UnitOfWork,
            vectorize_service: VectorizedService,
            vectorized_knowledge_service: VectorizedKnowledgeService
    ):
        self._uow = unit_of_work
        self._vectorize_service = vectorize_service
        self._vectorized_knowledge_service = vectorized_knowledge_service

    async def __call__(self, command: GetVectorizedDataCommand):
        logger.info("Started GetVectorizedDataCommandHandler")
        if command.vectorization_resources:
            task_list = [self._get_vectorized_data(resource) for resource in command.vectorization_resources]
            return (result for result in await asyncio.gather(*task_list))
        return tuple()

    async def _get_vectorized_data(self, resource: VectorizationResource):
        vector = await self._vectorize_service.get_vector(
            VectorizedKnowledgeResource(
                resource_id=resource.resource_id,
                content=resource.input_data
            )
        )
        logger.info("Finished GetVectorizedDataCommandHandler")

        result = await self._vectorized_knowledge_service.get_knn(
            resource_ids=[resource.resource_id],
            vectorized_query=vector,
            knowledge_base_id=resource.knowledge_base_id,
        )
        logger.info(f"Finished getting data for {resource.resource_id} with result: {result}")
        return {resource.resource_id: result.resources[0].content}