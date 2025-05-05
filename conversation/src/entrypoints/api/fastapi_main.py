from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.entrypoints.api import fastapi_handlers
from src.entrypoints.api.ioc import Container


class ServiceBootStrap:
    """
    Bootstrap class for initializing and configuring the FastAPI service.
    Handles dependency injection container setup and CORS middleware configuration.

    Attributes:
        API_ROUTE_PREFIX: Prefix for the FastAPI routes.
    """

    API_ROUTE_PREFIX: str = "/api"

    @staticmethod
    def create_service_api() -> FastAPI:
        """
        Creates and configures a new FastAPI application instance.

        Returns:
            FastAPI: Configured FastAPI application instance
        """
        container = Container()
        container.init_resources()
        service_api: FastAPI = FastAPI()
        service_api.container = container
        service_api.include_router(
            fastapi_handlers.router,
            prefix=ServiceBootStrap.API_ROUTE_PREFIX,
        )
        service_api.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        return service_api


app = ServiceBootStrap.create_service_api()
