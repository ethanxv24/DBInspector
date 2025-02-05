from db_inspector.checks.base import BaseCheck


class PgReplicationCheck(BaseCheck):
    def run(self, db_connection):
        """
        检查 PostgreSQL 的主从同步状态
        :param db_connection: PostgreSQL 数据库连接
        :return: 字典，包含检查结果
        """
        try:
            cursor = db_connection.cursor()
            cursor.execute("SELECT * FROM pg_stat_replication")
            replication_status = cursor.fetchall()
            if not replication_status:
                return {"status": "failure", "message": "No replication info found"}
            return {"status": "success", "message": "Replication is healthy"}
        except Exception as e:
            return {"status": "failure", "message": f"Replication check failed: {str(e)}"}
