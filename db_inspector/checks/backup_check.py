from db_inspector.checks.base import BaseCheck, CheckItem, Status, manage_transaction

CHECK_NAME = "备份检查"

class PgBackupCheck(BaseCheck):
    def run(self, db_connection):
        try:
            with manage_transaction(db_connection) as cursor:
                cursor.execute("SELECT pg_is_in_backup()")
                in_backup = cursor.fetchone()[0]
            if in_backup:
                return CheckItem(check_name=CHECK_NAME, status=Status.SUCCESS.value, message="Backup is in progress or completed.")
            return CheckItem(check_name=CHECK_NAME, status=Status.FAILURE.value, message="No backup in progress.")
        except Exception as e:
            return CheckItem(check_name=CHECK_NAME, status=Status.FAILURE.value, message=f"Backup check failed: {str(e)}")
