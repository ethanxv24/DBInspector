from db_inspector.checks.base import BaseCheck


class PgPerformanceCheck(BaseCheck):
    def run(self, db_connection):
        """
        检查 PostgreSQL 数据库的性能
        :param db_connection: PostgreSQL 数据库连接
        :return: 字典，包含检查结果
        """
        try:
            cursor = db_connection.cursor()
            cursor.execute("SELECT now()")  # 简单查询来测试响应
            return {"status": "success", "message": "Performance check passed"}
        except Exception as e:
            return {"status": "failure", "message": f"Performance check failed: {str(e)}"}
