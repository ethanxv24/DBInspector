from abc import abstractmethod


class BaseCheck:
    @abstractmethod
    def run(self, db_connection):
        raise NotImplementedError("This method should be overridden by subclasses")
