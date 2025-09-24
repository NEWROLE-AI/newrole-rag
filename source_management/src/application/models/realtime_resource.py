import enum
from dataclasses import dataclass, asdict
from enum import Enum


class RealtimeResourceType(Enum):
    """
    Enum representing types of realtime resources.

    - DATABASE: A connection to a relational database.
    - REST_API: A RESTful API endpoint.
    """
    DATABASE = "DATABASE"
    REST_API = "REST_API"


class DbType(enum.Enum):
    POSTGRESQL = "POSTGRESQL"
    MYSQL = "MYSQL"


@dataclass
class Database:
    connection_params: dict[str, str] | None = None
    query: str | None = None
    db_type: DbType | None = None
    secret_path: str | None = None


@dataclass
class RestApi:
    url: str | None = None
    method: str | None = None
    header: dict[str, str] | None = None
    payload: dict[str, str] | None = None
    query_params: dict[str, str] | None = None
    placeholders: dict[str, str] | None = None


@dataclass
class RealtimeResource:
    knowledge_base_id: str
    type: RealtimeResourceType
    user_id: str
    resource_id: str | None = None
    extra: Database | RestApi | None = None
