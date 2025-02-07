from db_inspector.checks.base import BaseCheck, Status, CheckItem, manage_transaction

CHECK_NAME = "表和索引统计检查"

class PgTableIndexCheck(BaseCheck):
    def run(self, db_connection):
        try:
            with manage_transaction(db_connection) as cursor:
                cursor.execute("SELECT relname, n_dead_tup FROM pg_stat_user_tables WHERE n_dead_tup > 10000")
                result = cursor.fetchall()
            if result:
                message = "Dead rows found in the following tables: " + ", ".join([f"{row[0]}" for row in result])
                return CheckItem(check_name=CHECK_NAME, status=Status.WARNING.value, message=message)
            return CheckItem(check_name=CHECK_NAME, status=Status.SUCCESS.value, message="No significant dead rows found")
        except Exception as e:
            return CheckItem(check_name=CHECK_NAME, status=Status.FAILURE.value, message=f"Table/index check failed: {str(e)}")
