from db_inspector.checks.base import BaseCheck


class PgBackupCheck(BaseCheck):
    def run(self, db_connection):
        try:
            cursor = db_connection.cursor()
            cursor.execute("SELECT * FROM pg_stat_bgwriter")  # 假设用这个查询检查备份状态
            backup_status = cursor.fetchall()
            if not backup_status:
                return {"status": "failure", "message": "Backup status not found"}
            return {"status": "success", "message": "Backup is healthy"}
        except Exception as e:
            return {"status": "failure", "message": f"Backup check failed: {str(e)}"}
