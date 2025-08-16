from abc import ABC, abstractmethod


class RealtimeDatabaseService(ABC):

    @abstractmethod
    async def execute_query(self, query: str, connection_params: dict) -> list[dict]:
        raise NotImplementedError