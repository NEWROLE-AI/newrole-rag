import traceback
from io import BytesIO

import PyPDF2
import requests
from aws_lambda_powertools import Logger
from docx import Document

from src.application.ports.file_processor import FileProcessor


logger = Logger("file_processor")


class FileProcessorImpl(FileProcessor):
    def __init__(self, token: str):
        self.token = token
        self.supported_types = {
            "application/pdf": self._process_pdf,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": self._process_docx,
        }

    def _process_pdf(self, file_content: bytes) -> str:
        try:
            pdf_file = BytesIO(file_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}")
            logger.error(traceback.format_exc())
            return ""

    def _process_docx(self, file_content: bytes) -> str:
        try:
            doc = Document(BytesIO(file_content))
            return "\n".join([paragraph.text for paragraph in doc.paragraphs])
        except Exception as e:
            logger.error(f"Error processing DOCX: {str(e)}")
            logger.error(traceback.format_exc())
            return ""

    def _download_file(self, file_url: str) -> bytes | None:
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(file_url, headers=headers)
            response.raise_for_status()
            return response.content
        except Exception as e:
            logger.error(f"Error downloading file: {str(e)}")
            return None

    def process_file(self, file_content: bytes, mime_type: str) -> str | None:
        processor = self.supported_types.get(mime_type)
        if processor:
            return processor(file_content)
        return None

    def process_files(self, files: list[dict]) -> str:
        processed_text = []

        for file in files:
            mime_type = file.get("mimetype", "")
            if mime_type in self.supported_types:
                file_content = self._download_file(file["url_private"])
                if file_content:
                    extracted_text = self.process_file(file_content, mime_type)
                    if extracted_text:
                        processed_text.append(
                            f"Content from {file['name']}:\n{extracted_text}"
                        )

        return "\n\n".join(processed_text)
