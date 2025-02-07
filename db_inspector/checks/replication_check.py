from db_inspector.checks.base import BaseCheck, CheckItem, Status, manage_transaction

CHECK_NAME="主从同步检查"

class PgReplicationCheck(BaseCheck):
    def run(self, db_connection):
        """
        检查 PostgreSQL 的主从同步状态
        :param db_connection: PostgreSQL 数据库连接
        :return: 字典，包含检查结果
        """
        try:
            with manage_transaction(db_connection) as cursor:
                cursor.execute("SELECT * FROM pg_stat_replication")
                replication_status = cursor.fetchall()
            if not replication_status:
                return CheckItem(check_name=CHECK_NAME, status=Status.FAILURE.value, message="No replication info found")
            return CheckItem(check_name=CHECK_NAME, status=Status.SUCCESS.value, message="Replication is healthy")
        except Exception as e:
            return CheckItem(check_name=CHECK_NAME, status=Status.FAILURE.value, message=f"Replication check failed: {str(e)}")
