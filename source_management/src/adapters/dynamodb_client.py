from aws_lambda_powertools import Logger
from boto3_type_annotations.dynamodb import Client

from src.application.exceptions.value_error_exception import CustomValueError, ErrorStatus
from src.application.ports.dynaodb_client import DynamodbClient

logger = Logger("dynamodb_client.py")

class DynamoDbClientImpl(DynamodbClient):

    def __init__(self, dynamodb_client: Client):
        self.dynamodb_client = dynamodb_client

    def check_connection(self, table_name):
        logger.info(f"Checking connection to dynamodb table: {table_name}")
        try:
            self.dynamodb_client.Table(table_name).load()
        except Exception as e:
            logger.error(f"Error connecting to dynamodb table: {str(e)}")
            raise CustomValueError(error_status=ErrorStatus.NOT_FOUND, message=f"Error connecting to dynamodb table: {str(e)}")