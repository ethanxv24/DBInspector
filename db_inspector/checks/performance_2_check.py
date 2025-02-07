from db_inspector.checks.base import BaseCheck, CheckItem, Status, manage_transaction

CHECK_NAME = "性能检查2"

class PgPerformance2Check(BaseCheck):
    def run(self, db_connection):
        try:
            with manage_transaction(db_connection) as cursor:
                cursor.execute("SELECT name, setting FROM pg_settings WHERE name = 'shared_buffers'")
                shared_buffers = cursor.fetchone()[1]
                cursor.execute("SELECT name, setting FROM pg_settings WHERE name = 'effective_cache_size'")
                effective_cache_size = cursor.fetchone()[1]
            # 检查 shared_buffers 是否合理（假设 8 GB 为合理大小）
            if int(shared_buffers.split(' ')[0]) < 8:
                return CheckItem(check_name=CHECK_NAME, status=Status.WARNING.value, message=f"shared_buffers ({shared_buffers}) is too small.")
            return CheckItem(check_name=CHECK_NAME, status=Status.SUCCESS.value, message=f"Performance parameters are optimal. shared_buffers: {shared_buffers}, effective_cache_size: {effective_cache_size}")
        except Exception as e:
            return CheckItem(check_name=CHECK_NAME, status=Status.FAILURE.value, message=f"Performance check failed: {str(e)}")
