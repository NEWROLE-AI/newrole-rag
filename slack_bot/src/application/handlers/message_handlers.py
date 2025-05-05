from aws_lambda_powertools import Logger

from src.application.ports.file_processor import FileProcessor
from src.application.services.conversation_service import ConversationService


logger = Logger(service="MessageHandler")


class MessageHandler:
    def __init__(self, conversation_service: ConversationService, file_processor: FileProcessor):
        self.conversation_service = conversation_service
        self.file_processor = file_processor

    def handle(self, event, say, bot_id):
        try:
            logger.info("Handling message event", extra={"event": event})
            channel_type = event.get("channel_type")
            user_id = event.get("user")
            text = event.get("text", "")
            channel_id = event["channel"]
            files = event.get("files", [])

            # Process any attached files
            file_content = ""
            if files:
                file_content = self.file_processor.process_files(files)
                if file_content:
                    text = f"{text}\n\nAttached documents content:\n{file_content}"

            if channel_type == "channel":
                logger.info("Processing message in a public channel",
                            extra={"channel_id": channel_id, "text": text})
                if f'<@{bot_id}>' in text:
                    response = self.conversation_service.process_message(
                        channel_id, text, user_id
                    )
                    logger.info("Response generated", extra={"response": response})
                    say(response)

            elif channel_type == "im":
                logger.info("Processing direct message",
                            extra={"channel_id": channel_id, "text": text, "user_id": user_id})
                response = self.conversation_service.process_message(channel_id, text, user_id)
                logger.info("Response generated for direct message", extra={"response": response})
                say(response)
        except Exception as e:
            logger.exception(e)