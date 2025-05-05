from abc import ABC, abstractmethod


class FileProcessor(ABC):

    @abstractmethod
    def process_file(self, file_content: bytes, mime_type: str) -> str | None:
        raise NotImplementedError

    @abstractmethod
    def process_files(self, files: list[dict]) -> str | None:
        raise NotImplementedError
