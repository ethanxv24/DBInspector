from abc import abstractmethod
from enum import Enum


class Status(Enum):
    SUCCESS = 'success'
    FAILURE = 'failure'
    WARNING = 'warning'

class CheckItem:
    def __init__(self, check_name, status,message):
        self.check_name = check_name
        self.status = status
        self.message = message

class BaseCheck:
    @abstractmethod
    def run(self, db_connection):
        raise NotImplementedError("This method should be overridden by subclasses")
