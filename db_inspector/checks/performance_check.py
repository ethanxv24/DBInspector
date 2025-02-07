from db_inspector.checks.base import BaseCheck, CheckItem, Status, manage_transaction

CHECK_NAME="性能检查"

class PgPerformanceCheck(BaseCheck):
    def run(self, db_connection):
        """
        检查 PostgreSQL 数据库的性能
        :param db_connection: PostgreSQL 数据库连接
        :return: 字典，包含检查结果
        """
        try:
            with manage_transaction(db_connection) as cursor:
                cursor.execute("SELECT now()")  # 简单查询来测试响应
            return CheckItem(check_name=CHECK_NAME, status=Status.SUCCESS.value, message="Performance check passed")
        except Exception as e:
            return CheckItem(check_name=CHECK_NAME, status=Status.FAILURE.value, message=f"Performance check failed: {str(e)}")
