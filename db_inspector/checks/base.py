from abc import abstractmethod
from enum import Enum
from contextlib import contextmanager


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


@contextmanager
def manage_transaction(connection):
    cursor = connection.cursor()
    try:
        yield cursor
        connection.commit()  # 正常结束时提交事务
    except Exception as exc:
        connection.rollback()  # 出错时回滚事务
        raise exc
    finally:
        cursor.close()
