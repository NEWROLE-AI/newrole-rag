from abc import ABC, abstractmethod


class DynamodbClient(ABC):

    @abstractmethod
    def check_connection(self, table_name):
        raise NotImplementedError()
