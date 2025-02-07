from db_inspector.checks.base import BaseCheck, Status, CheckItem, manage_transaction

CHECK_NAME = "WAL 日志检查"

class PgWALCheck(BaseCheck):
    def run(self, db_connection):
        try:
            with manage_transaction(db_connection) as cursor:
                cursor.execute("SHOW archive_mode")
                archive_mode = cursor.fetchone()[0]
            if archive_mode != "on":
                return CheckItem(check_name=CHECK_NAME, status=Status.FAILURE.value, message="WAL archive mode is off")
            return CheckItem(check_name=CHECK_NAME, status=Status.SUCCESS.value, message="WAL archive mode is enabled")
        except Exception as e:
            return CheckItem(check_name=CHECK_NAME, status=Status.FAILURE.value, message=f"WAL check failed: {str(e)}")
