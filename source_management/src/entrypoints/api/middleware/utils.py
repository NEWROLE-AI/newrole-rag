import json
import base64
import asyncio
import traceback
from typing import Callable, Awaitable, Any, Type


from pydantic import BaseModel
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.parser import parse, ValidationError
from aws_lambda_powertools.utilities.typing import LambdaContext

from src.application.exceptions.value_error_exception import (
    ErrorStatus,
    CustomValueError,
)

logger = Logger()


# Lambda Handler Middleware
def lambda_handler_decorator(
    model: Type[BaseModel],
) -> Callable[
    [Callable[..., Awaitable[BaseModel]]],
    Callable[[dict[str, Any], LambdaContext], dict[str, Any]],
]:
    """
    Decorator for AWS Lambda handlers that provides request validation and error handling.

    Args:
        model: Pydantic model class for request validation

    Returns:
        Callable: Decorated handler function
    """

    def decorator(
        handler: Callable[..., Awaitable[BaseModel]]
    ) -> Callable[[dict[str, Any], LambdaContext], dict[str, Any]]:
        def wrapper(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
            loop = asyncio.get_event_loop()
            try:
                # Extract and merge parameters from different sources
                path_parameters = event.get("pathParameters", {}) or {}
                body_raw = event.get("body")
                if body_raw:
                    try:
                        body_parameters = json.loads(body_raw) or {}
                    except json.JSONDecodeError:
                        body_parameters = json.loads(base64.b64decode(event["body"]))
                else:
                    body_parameters = {}
                query_parameters = event.get("queryStringParameters", {}) or {}

                # Combine all parameters
                event_data = {
                    **path_parameters,
                    **body_parameters,
                    **query_parameters,
                }
                # Validate and process request
                request = parse(model=model, event=event_data)
                result = loop.run_until_complete(handler(request))

                return {
                    "statusCode": 200,
                    "headers": {
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Headers": "Content-Type",
                        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE",
                    },
                    "body": json.dumps(result.model_dump(exclude_none=True)),
                }
            except ValidationError as e:
                logger.error(msg=f"Validation error: {e}")
                return {
                    "statusCode": 400,
                    "headers": {
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Headers": "Content-Type",
                        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE",
                    },
                    "body": json.dumps(
                        {"__type": "Validation error", "message": str(e)}
                    ),
                }
            except CustomValueError as e:
                logger.error(msg=traceback.format_exc())

                status_code_errors = {
                    ErrorStatus.NOT_FOUND: 404,
                    ErrorStatus.BAD_REQUEST: 400,
                }
                return {
                    "statusCode": status_code_errors[e.error_status],
                    "headers": {
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Headers": "Content-Type",
                        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE",
                    },
                    "body": json.dumps({"__type": "ValueError", "message": str(e)}),
                }
            except Exception as e:
                logger.error(msg=traceback.format_exc())
                return {
                    "statusCode": 500,
                    "headers": {
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Headers": "Content-Type",
                        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE",
                    },
                    "body": json.dumps(
                        {"__type": "InternalServerError", "message": ""}
                    ),
                }

        return wrapper

    return decorator
