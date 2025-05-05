from abc import ABC, abstractmethod


class GoogleDriveClient(ABC):
    """
    Abstract base class for Google Drive api.

    Defines the contract for calls to google drive
    """

    @abstractmethod
    def check_google_drive(self, google_drive_url: str) -> None:
        """
        Abstract method to validate Google Drive url.

        Args:
            google_drive_url (str): Google Drive url.
        """
        raise NotImplementedError
