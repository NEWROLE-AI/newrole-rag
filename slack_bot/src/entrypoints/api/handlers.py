from aws_lambda_powertools import Logger
from dependency_injector.wiring import inject, Provide
from slack_bolt.adapter.aws_lambda import SlackRequestHandler
from src.entrypoints.api import ioc

from fastapi import Request, FastAPI

from src.entrypoints.api.ioc import Container

logger = Logger(service="handlers")


def handle_ack(ack):
    ack()


def handle_message(event, say):
    logger.info("Handling Slack 'message' event", extra={"event": event, "say": say})
    try:
        bot_id = container.slack_app().client.auth_test().get("user_id")
        result = container.message_handler().handle(event, say, bot_id)
        logger.info("MessageHandler processed 'message' event successfully")
        return result
    except Exception as e:
        logger.exception("Error while handling 'message' event")
        raise e


def handle_member_joined(event, say):
    """Handler for Slack 'member_joined_channel' event"""
    logger.info("Handling Slack 'member_joined_channel' event", extra={"event": event})
    try:
        client = container.slack_app().client
        bot_id = client.auth_test().get("user_id")
        container.channel_handler().handle(event, say, client, bot_id)
        logger.info(
            "ChannelHandler processed 'member_joined_channel' event successfully"
        )
    except Exception as e:
        logger.exception("Error while handling 'member_joined_channel' event")
        raise e


@inject
def handler(event, context, app=Provide[Container.slack_app]):
    """AWS Lambda handler"""
    logger.info("Received Lambda event", extra={"event": event})
    logger.info(app)
    try:
        app.event("message")(ack=handle_ack, lazy=[handle_message])
        app.event("member_joined_channel")(ack=handle_ack, lazy=[handle_member_joined])

        slack_handler = SlackRequestHandler(app=app)
        response = slack_handler.handle(event, context)
        logger.info(
            "SlackRequestHandler processed the event successfully",
            extra={"response": response},
        )
        return response
    except Exception as e:
        logger.exception("Error while handling the Lambda event")
        raise e


container = Container()
container.wire(modules=[__name__])
logger.info("Dependency injection container wired successfully")
