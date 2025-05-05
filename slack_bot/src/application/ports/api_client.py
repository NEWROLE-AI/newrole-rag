from abc import ABC, abstractmethod


class ConversationApiClient(ABC):
    @abstractmethod
    def send_message(self, conversation_id: str, message: str, user_id: str):
        raise NotImplementedError


class ResourceManagerApiClient(ABC):
    @abstractmethod
    def add_resource(self, channel_id: str, messages: list[dict]):
        raise NotImplementedError
