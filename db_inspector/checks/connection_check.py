from tabnanny import check

from db_inspector.checks.base import BaseCheck, CheckItem, Status, manage_transaction

CHECK_NAME="连接检查"

class PgConnectionCheck(BaseCheck):
    def run(self, db_connection):
        """
        检查数据库连接是否正常
        :param db_connection: PostgreSQL 数据库连接
        :return: 字典，包含检查结果
        """
        try:
            with manage_transaction(db_connection) as cursor:
                cursor.execute("SELECT 1")
            return CheckItem(check_name=CHECK_NAME, status=Status.SUCCESS.value, message="Connection successful")
        except Exception as e:
            return CheckItem(check_name=CHECK_NAME, status=Status.FAILURE.value, message=f"Connection failed: {str(e)}")
