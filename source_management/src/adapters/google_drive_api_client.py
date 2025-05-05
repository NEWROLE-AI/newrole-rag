from aws_lambda_powertools import Logger
from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError

from src.application.exceptions.value_error_exception import CustomValueError, ErrorStatus
from src.application.ports.google_drive_client import GoogleDriveClient


logger = Logger(service="google_drive_api_client")

class ApiGoogleDriveClient(GoogleDriveClient):
    """
    A service class to manage operations with Google Drive storage.

    This class uses googleapiclient to interact with the Google Drive repository and is intended to be used
    in the context of working with knowledge base related resources.
    """

    def __init__(self, google_drive_client: Resource):
        """
        Initializes the HttpGoogleDriveApiClient with a given googleapiclient.

        Args:
            google_drive_client (AsyncSession): The googleapiclient.discovery.Resource instance.
        """
        self.google_drive_client = google_drive_client

    async def check_google_drive(self, google_drive_url: str) -> None:
        """
        Validation of the Google Drive url. If url isn't a Google Drive folder, an error is raised.

        Args:
            google_drive_url (str): Google Drive url.

        Raises:
            CustomValueError: If url isn't a Google Drive folder.
        """
        if google_drive_url.strip("https://").strip("http://").startswith("drive.google.com") and 'folders' in google_drive_url:
            drive_id = google_drive_url.split('folders/')[1].split('?')[0]
        else:
            raise CustomValueError(error_status=ErrorStatus.BAD_REQUEST, message="Incorrect URL format. Make sure it is a link to a Google Drive folder.")

        try:
            self.google_drive_client.files().get(fileId=drive_id, fields="id").execute()
        except HttpError as error:
            if error.resp.status in [403, 401]:
                raise CustomValueError(error_status=ErrorStatus.BAD_REQUEST, message="Folder access error in google drive")
            elif error.resp.status == 404:
                raise CustomValueError(error_status=ErrorStatus.NOT_FOUND, message="Folder not found in google drive")