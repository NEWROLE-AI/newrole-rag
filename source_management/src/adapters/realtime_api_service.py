from typing import Any

import aiohttp

from src.application.models.realtime_resource import RestApi
from src.application.ports.realtime_api_service import RealtimeApiService


class IoHttpRealtimeApiService(RealtimeApiService):

    def __init__(self, session: aiohttp.ClientSession):
        self._session = session

    async def get_data(self, rest_api: RestApi) -> str:
        """
        realtime_api: The realtime API to call.

        Send a request to the realtime API.
        """
        if RestApi.placeholders:
            rest_api.url = rest_api.url.format(**RestApi.placeholders)

        if rest_api.method == "GET":
            async with self._session.get(rest_api.url, params=rest_api.query_params, headers=rest_api.header) as response:
                return await response.text()
        elif rest_api.method == "POST":
            async with self._session.post(rest_api.url, json=rest_api.payload, params=rest_api.query_params, headers=rest_api.header) as response:
                return await response.text()
        else:
            raise NotImplementedError("This method is not supported.")

