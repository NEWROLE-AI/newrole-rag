import os
import gzip
import shutil
import boto3
from urllib.request import urlretrieve
from boto3_type_annotations.s3 import Client
from aws_lambda_powertools import Logger
import fasttext

# Constants for model configuration
DEFAULT_MODEL_PATH = "./tmp/cc.en.300.bin"
FASTTEXT_MODEL_URL = "https://dl.fbaipublicfiles.com/fasttext/vectors-crawl/cc.en.300.bin.gz"

logger = Logger(service="fasttext_vectorizer")


class FastTextVectorizer:
    model = None

    def __init__(
            self,
            client: Client = None,
            bucket_name: str = None,
            model_s3_key: str = None,
            local_model_path: str = DEFAULT_MODEL_PATH,
            model_url: str = FASTTEXT_MODEL_URL,
    ):
        """
        Initialize the FastText vectorizer

        Args:
            client: S3 client for model download (optional)
            bucket_name: S3 bucket containing the model (optional)
            model_s3_key: S3 key for the model file (optional)
            local_model_path: Path to store the downloaded model
            model_url: URL to download the model from if not in S3
        """
        self._client = client
        self.bucket_name = bucket_name
        self.model_s3_key = model_s3_key
        self.local_model_path = local_model_path
        self.model_url = model_url
        self.model = None
        if client:
            self.s3_client = boto3.client("s3")

        self.load_model()

    def _download_from_url(self, show_progress: bool = True):
        """
        Download the FastText model from official URL

        Args:
            show_progress: Whether to show download progress
        """
        gz_path = self.local_model_path + ".gz"

        # Create directory if not exists
        os.makedirs(os.path.dirname(self.local_model_path), exist_ok=True)

        logger.info(f"Downloading model from {self.model_url}")

        def progress_hook(block_num, block_size, total_size):
            """Show download progress"""
            if show_progress and total_size > 0:
                downloaded = block_num * block_size
                percent = min(100, downloaded * 100 / total_size)
                logger.info(f"Download progress: {percent:.1f}%")

        # Download compressed model
        urlretrieve(self.model_url, gz_path, reporthook=progress_hook if show_progress else None)

        logger.info(f"Extracting model from {gz_path}")

        # Extract .gz file
        with gzip.open(gz_path, 'rb') as f_in:
            with open(self.local_model_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

        # Remove compressed file to save space
        os.remove(gz_path)

        logger.info(f"Model extracted to {self.local_model_path}")

    def _download_model_from_s3(self):
        """Download the FastText model from S3 if not present locally"""
        if not os.path.exists(self.local_model_path):
            logger.info(f"Downloading model from S3: {self.bucket_name}/{self.model_s3_key}")
            os.makedirs(os.path.dirname(self.local_model_path), exist_ok=True)
            self.s3_client.download_file(
                Bucket=self.bucket_name,
                Key=self.model_s3_key,
                Filename=self.local_model_path,
            )
            logger.info("Model downloaded from S3")

    def _ensure_model_exists(self):
        """
        Ensure model file exists locally, download if necessary
        Priority: local file -> S3 -> public URL
        """
        if os.path.exists(self.local_model_path):
            logger.info(f"Model already exists at {self.local_model_path}")
            return

        # Try S3 first if configured
        if self._client and self.bucket_name and self.model_s3_key:
            try:
                self._download_model_from_s3()
                return
            except Exception as e:
                logger.warning(f"Failed to download from S3: {e}")

        # Fallback to public URL
        logger.info("Downloading model from public URL")
        self._download_from_url()

    def load_model(self, force_download: bool = False):
        """
        Load the FastText model into memory

        Args:
            force_download: Force re-download even if file exists
        """
        if force_download and os.path.exists(self.local_model_path):
            logger.info("Removing existing model file for re-download")
            os.remove(self.local_model_path)

        self._ensure_model_exists()

        logger.info(f"Loading model from {self.local_model_path}")
        FastTextVectorizer.model = fasttext.load_model(self.local_model_path)
        logger.info(f"Model loaded successfully. Vocab size: {len(FastTextVectorizer.model.words)}")

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

