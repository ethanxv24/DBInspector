from db_inspector.checks.base import BaseCheck, CheckItem, Status, manage_transaction

# 1. 失效的数据槽检查
CHECK_NAME_SLOT = "失效的数据槽检查"

class PgReplicationSlotCheck(BaseCheck):
    def run(self, db_connection):
        """
        查看是否存在失效的数据槽
        :param db_connection: PostgreSQL 数据库连接
        :return: CheckItem，包含检查结果
        """
        try:
            with manage_transaction(db_connection) as cursor:
                cursor.execute("select slot_name, plugin, database from pg_replication_slots where active='f'")
                inactive_slots = cursor.fetchall()
            if inactive_slots:
                # 将失效的数据槽名称拼接到提示信息中
                slot_names = ', '.join([slot[0] for slot in inactive_slots])
                return CheckItem(check_name=CHECK_NAME_SLOT,
                                 status=Status.FAILURE.value,
                                 message=f"发现失效的数据槽: {slot_names}")
            else:
                return CheckItem(check_name=CHECK_NAME_SLOT,
                                 status=Status.SUCCESS.value,
                                 message="未发现失效的数据槽")
        except Exception as e:
            return CheckItem(check_name=CHECK_NAME_SLOT,
                             status=Status.FAILURE.value,
                             message=f"失效的数据槽检查失败: {str(e)}")
