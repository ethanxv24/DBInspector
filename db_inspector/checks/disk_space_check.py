from db_inspector.checks.base import BaseCheck, CheckItem, Status, manage_transaction

CHECK_NAME = "磁盘空间检查"

class PgDiskSpaceCheck(BaseCheck):
    def run(self, db_connection):
        try:
            with manage_transaction(db_connection) as cursor:
                cursor.execute("SELECT pg_size_pretty(pg_database_size(current_database()))")
                db_size = cursor.fetchone()[0]
            # 假设数据库大小限制为 100 GB
            if db_size > '100 GB':
                return CheckItem(check_name=CHECK_NAME, status=Status.WARNING.value, message=f"Database size {db_size} exceeds the limit.")
            return CheckItem(check_name=CHECK_NAME, status=Status.SUCCESS.value, message=f"Database size is within limits: {db_size}")
        except Exception as e:
            return CheckItem(check_name=CHECK_NAME, status=Status.FAILURE.value, message=f"Disk space check failed: {str(e)}")
