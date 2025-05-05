import os
import boto3

from boto3_type_annotations.s3 import Client
from aws_lambda_powertools import Logger
import fasttext

# Constants for model configuration
DEFAULT_MODEL_PATH = "./tmp/cc.en.300.bin"

logger = Logger(service="fasttext_vectorizer")


class FastTextVectorizer:
    model = None

    def __init__(
        self,
        client: Client,
        bucket_name: str,
        model_s3_key: str,
        local_model_path: str = DEFAULT_MODEL_PATH,
    ):
        """
        Initialize the FastText vectorizer

        Args:
            client: S3 client for model download
            bucket_name: S3 bucket containing the model
            model_s3_key: S3 key for the model file
            chunk_size: Size of text chunks for processing
            batch_size: Number of chunks to process simultaneously
            max_workers: Number of parallel processing threads
            local_model_path: Path to store the downloaded model
        """
        self._client = client
        self.bucket_name = bucket_name
        self.model_s3_key = model_s3_key
        self.local_model_path = local_model_path
        self.model = None
        self.s3_client = boto3.client("s3")

    def _download_model_from_s3(self):
        """Download the FastText model from S3 if not present locally"""
        if not os.path.exists(self.local_model_path):
            self.s3_client.download_file(
                Bucket=self.bucket_name,
                Key=self.model_s3_key,
                Filename=self.local_model_path,
            )

    def load_model(self, model_url):
        """
        Load the FastText model into memory

        Args:
            model_url: URL or path to the model
        """
        logger.info(f"Loading model from {self.local_model_path}")
        self._download_model_from_s3()
        FastTextVectorizer.model = fasttext.load_model(self.local_model_path)
        logger.info(f"Loaded model from {self.model}")

    async def vectorize_text(self, text: str) -> list:
        """
        Vectorize a single text (for small texts)

        Args:
            text: Text to vectorize

        Returns:
            list representing the text vector
        """
        if FastTextVectorizer.model is None:
            logger.error("Model not loaded before use")
            raise ValueError("Model is not loaded. Call `load_model` first.")
        clean_text = text.replace("\n", " ").strip()
        vector = FastTextVectorizer.model.get_sentence_vector(clean_text)
        return vector.tolist()
