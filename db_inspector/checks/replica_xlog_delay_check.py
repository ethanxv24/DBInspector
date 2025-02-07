from db_inspector.checks.base import BaseCheck, CheckItem, Status, manage_transaction

CHECK_NAME_REPLICA_DELAY = "从库延迟xlog检查"

class PgReplicaXlogDelayCheck(BaseCheck):
    def run(self, db_connection):
        """
        检查从库延迟xlog的大小（需在主库执行）
        :param db_connection: PostgreSQL 数据库连接
        :return: CheckItem，包含检查结果
        """
        try:
            with manage_transaction(db_connection) as cursor:
                cursor.execute(
                    "select client_addr, pg_xlog_location_diff(pg_current_xlog_location(), replay_location)/1024/1024 as delay_mb "
                    "from pg_stat_replication"
                )
                results = cursor.fetchall()
            if results:
                message_lines = []
                for row in results:
                    message_lines.append(f"Client {row[0]} 延迟: {row[1]:.2f} MB")
                message = "\n".join(message_lines)
                return CheckItem(check_name=CHECK_NAME_REPLICA_DELAY,
                                 status=Status.SUCCESS.value,
                                 message=message)
            else:
                return CheckItem(check_name=CHECK_NAME_REPLICA_DELAY,
                                 status=Status.FAILURE.value,
                                 message="未查询到从库延迟xlog数据")
        except Exception as e:
            return CheckItem(check_name=CHECK_NAME_REPLICA_DELAY,
                             status=Status.FAILURE.value,
                             message=f"从库延迟xlog检查失败: {str(e)}")
