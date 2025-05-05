from dataclasses import dataclass
from enum import Enum


class ErrorStatus(str, Enum):
    """Statuses of CustomValueError"""
    NOT_FOUND = 'NOT_FOUND'
    BAD_REQUEST = 'BAD_REQUEST'


@dataclass
class CustomValueError(ValueError):
    """Exception raised for value errors."""
    message: str
    error_status: ErrorStatus

    def __str__(self):
        return f'{self.message}'