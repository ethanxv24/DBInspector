from db_inspector.checks.base import BaseCheck


class PgConnectionCheck(BaseCheck):
    def run(self, db_connection):
        """
        检查数据库连接是否正常
        :param db_connection: PostgreSQL 数据库连接
        :return: 字典，包含检查结果
        """
        try:
            cursor = db_connection.cursor()
            cursor.execute("SELECT 1")
            return {"status": "success", "message": "Connection successful"}
        except Exception as e:
            return {"status": "failure", "message": f"Connection failed: {str(e)}"}
