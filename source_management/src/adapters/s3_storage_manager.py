from aws_lambda_powertools import Logger
from boto3_type_annotations.s3 import Client  # type: ignore
from botocore.exceptions import ClientError

from src.application.exceptions.storage_exception import StorageException
from src.application.ports.storage_manager import StorageManager


# Logger instance to log S3 related actions
logger = Logger("s3_storage_manager")


class S3StorageManager(StorageManager):
    """
    A service class for managing S3 storage operations such as generating presigned URLs for uploading files.

    This class uses AWS SDK (Boto3) to interact with S3 storage, and it is intended to be used
    in the context of handling resources related to knowledge bases.
    """

    def __init__(self, client: Client, bucket_name: str):
        """
        Initializes the S3StorageManager with a specific S3 client and bucket name.

        Args:
            client (Client): The Boto3 S3 client instance.
            bucket_name (str): The name of the S3 bucket.
        """
        self.s3_client = client
        self.bucket_name = bucket_name

    async def generate_presigned_url(
        self, knowledge_base_name: str, resource_name: str, file_type: str
    ) -> str:
        """
        Generates a presigned URL for uploading a resource file to S3.

        Args:
            knowledge_base_name (str): The name of the knowledge base.
            resource_name (str): The name of the resource file.
            file_type (str): The file extension/type (e.g., 'pdf', 'jpg').

        Returns:
            str: A presigned URL that can be used to upload the resource file to S3.

        Raises:
            StorageException: If the presigned URL generation fails.
        """
        key = f"{knowledge_base_name}/{resource_name}.{file_type}"
        logger.info(f"Generating presigned URL for upload.")
        params = {
            "Bucket": self.bucket_name,
            "Key": key,
        }
        try:
            # Generate the presigned URL for a PUT operation
            url = self.s3_client.generate_presigned_url(
                "put_object", Params=params, ExpiresIn=3600
            )
            logger.info(f"Presigned URL generated successfully. Key: {key}")
        except ClientError as e:
            # If an error occurs, log it and raise a StorageException
            logger.error(f"Failed to generate presigned URL. Key: {key}, Error: {e}")
            raise StorageException(f"Failed to generate presigned url: {e}")
        return url
