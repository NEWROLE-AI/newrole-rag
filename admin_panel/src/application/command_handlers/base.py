from abc import ABC
from typing import TypeVar, Generic
from src.application.commands.base import BaseCommand


# Define a type variable TCommand that is bounded by the BaseCommand class.
# This allows for type-safe handling of command objects within the command handler.
TCommand = TypeVar("TCommand", bound=BaseCommand)


class BaseCommandHandler(ABC, Generic[TCommand]):
    """
    Abstract base class for command handlers. This is a generic handler class
    that processes commands of type TCommand (which is a subclass of BaseCommand).

    Subclasses should implement the __call__ method to handle specific command logic.
    """

    async def __call__(self, command: TCommand):
        """
        Handle the given command.

        Args:
            command (TCommand): The command to be processed.

        Raises:
            NotImplementedError: This method should be overridden by subclasses to implement command handling logic.
        """
        raise NotImplementedError
