from aws_lambda_powertools import Logger
from slack_bolt.adapter.aws_lambda import SlackRequestHandler
from slack_bolt.adapter.fastapi import SlackRequestHandler as FastApiSlackRequestHandler
from src.entrypoints.api import ioc

from fastapi import Request, FastAPI

logger = Logger(service="handlers")

app_handler = FastApiSlackRequestHandler(ioc.slack_app)
fastapi_app = FastAPI()


def handle_ack(ack):
    ack()


@ioc.slack_app.event("message")
def handle_message(event, say):
    logger.info("Handling Slack 'message' event", extra={"event": event, "say": say})
    try:
        bot_id = ioc.slack_app.client.auth_test().get("user_id")
        result = ioc.message_handler.handle(event, say, bot_id)
        logger.info("MessageHandler processed 'message' event successfully")
        return result
    except Exception as e:
        logger.exception("Error while handling 'message' event")
        raise e


@ioc.slack_app.event("member_joined_channel")
def handle_member_joined(event, say):
    """Handler for Slack 'member_joined_channel' event"""
    logger.info("Handling Slack 'member_joined_channel' event", extra={"event": event})
    try:
        client = ioc.slack_app.client
        bot_id = ioc.slack_app.client.auth_test().get("user_id")
        ioc.channel_handler.handle(event, say, client, bot_id)
        logger.info("ChannelHandler processed 'member_joined_channel' event successfully")
    except Exception as e:
        logger.exception("Error while handling 'member_joined_channel' event")
        raise e


def handler(event, context):
    """AWS Lambda handler"""
    logger.info("Received Lambda event", extra={"event": event})
    app = ioc.slack_app
    try:
        ioc.slack_app.event("message")(ack=handle_ack, lazy=[handle_message])
        slack_handler = SlackRequestHandler(app=app)
        response = slack_handler.handle(event, context)
        logger.info("SlackRequestHandler processed the event successfully", extra={"response": response})
        return response
    except Exception as e:
        logger.exception("Error while handling the Lambda event")
        raise e


@fastapi_app.post("/slack/events")
async def endpoint(req: Request):
    try:
        return await app_handler.handle(req)
    except Exception as e:
        logger.exception("Error while handling 'endpoint' event")
        raise e


# container = Container()
# container.wire(modules=[__name__])
logger.info("Dependency injection container wired successfully")
