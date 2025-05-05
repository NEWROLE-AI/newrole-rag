import uuid
from datetime import datetime
from typing import Any

from aws_lambda_powertools import Logger

from src.application.services.channel_service import ChannelService

logger = Logger(service="ChannelHandler")


class ChannelHandler:
    def __init__(self, channel_service: ChannelService):
        self.channel_service = channel_service

    def handle(self, event, say, client, bot_id):
        logger.info("Handling channel event", extra={"event": event})
        channel_id = event["channel"]
        logger.info("Storing channel history", extra={"channel_id": channel_id})

        # Get messages from Slack channel
        if bot_id == event["user"]:
            messages = self._get_channel_messages(client, channel_id)

            messages_with_replies = self._fetch_thread_replies(
                client, channel_id, messages
            )

            # Transform messages to required format
            formatted_messages = self._format_messages(messages_with_replies)

            # Get channel history through Slack API
            self.channel_service.store_channel_history(channel_id, formatted_messages)
            logger.info(
                "Channel history stored successfully", extra={"channel_id": channel_id}
            )
            say(
                "Hi. I've saved the history of the channel and I'm ready to help. Use @bot to contact me"
            )

    def _get_channel_messages(self, client, channel_id: str) -> list[dict]:
        """Fetch messages from Slack channel."""
        try:
            result = client.conversations_history(channel=channel_id)
            return result["messages"]
        except Exception as e:
            logger.error(
                "Failed to fetch channel messages",
                extra={"channel_id": channel_id, "error": str(e)},
            )
            raise

    def _fetch_thread_replies(
        self, client, channel_id: str, messages: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Fetch thread replies for messages that have threads."""
        messages_with_replies = []

        for message in messages:
            try:
                # Add the original message
                message_with_replies = message.copy()

                # Check if message has replies
                if message.get("thread_ts"):
                    # If this is already a thread reply, skip it as it will be handled with its parent
                    if message.get("thread_ts") != message.get("ts"):
                        continue

                    # Fetch replies for this thread
                    replies = client.conversations_replies(
                        channel=channel_id, ts=message["thread_ts"]
                    )

                    # Store replies in the message
                    if replies and "messages" in replies:
                        # Remove the parent message from replies as we already have it
                        thread_replies = [
                            reply
                            for reply in replies["messages"]
                            if reply.get("ts") != message.get("thread_ts")
                        ]
                        message_with_replies["replies"] = thread_replies

                messages_with_replies.append(message_with_replies)

            except Exception as e:
                logger.warning(
                    "Failed to fetch thread replies",
                    extra={
                        "message_ts": message.get("ts"),
                        "channel_id": channel_id,
                        "error": str(e),
                    },
                )
                messages_with_replies.append(message)
                continue

        return messages_with_replies

    def _format_messages(self, messages: list[dict]) -> list[dict]:
        """Transform Slack messages into required dictionary format."""
        formatted_messages = []

        for msg in messages:
            try:
                formatted_message = {
                    "message_id": str(uuid.uuid4()),
                    "content": msg.get("text", ""),
                    "user_id": msg.get("user", ""),
                    "timestamp": datetime.fromtimestamp(
                        float(msg.get("ts", 0))
                    ).isoformat(),
                    "thread_id": msg.get("thread_ts", ""),
                    "replies": [],
                }
                if "replies" in msg:
                    for reply in msg["replies"]:
                        formatted_reply = {
                            "message_id": str(uuid.uuid4()),
                            "content": reply.get("text", ""),
                            "user_id": reply.get("user", ""),
                            "timestamp": datetime.fromtimestamp(
                                float(reply.get("ts", 0))
                            ).isoformat(),
                            "thread_id": reply.get("thread_ts", ""),
                            "parent_message_id": formatted_message["message_id"],
                        }
                        formatted_message["replies"].append(formatted_reply)

                formatted_messages.append(formatted_message)
            except Exception as e:
                logger.warning(
                    "Failed to format message", extra={"message": msg, "error": str(e)}
                )
                continue

        return formatted_messages
