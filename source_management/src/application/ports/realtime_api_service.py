from abc import ABC, abstractmethod
from typing import Any

from src.application.models.realtime_resource import RestApi


class RealtimeApiService(ABC):

    @abstractmethod
    async def get_data(self, rest_api: RestApi) -> str:
        raise NotImplementedError