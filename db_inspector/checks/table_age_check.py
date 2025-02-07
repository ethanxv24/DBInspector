from db_inspector.checks.base import BaseCheck, CheckItem, Status, manage_transaction

CHECK_NAME_TABLE_AGE = "表剩余年龄检查"

class PgTableAgeCheck(BaseCheck):
    def run(self, db_connection):
        """
        查看表剩余年龄（返回剩余年龄最高的前5个表）
        :param db_connection: PostgreSQL 数据库连接
        :return: CheckItem，包含检查结果
        """
        try:
            with manage_transaction(db_connection) as cursor:
                cursor.execute(
                    "select current_database(), rolname, nspname, relkind, relname, age(relfrozenxid), "
                    "2^31 - age(relfrozenxid) as age_remain "
                    "from pg_authid t1 join pg_class t2 on t1.oid=t2.relowner "
                    "join pg_namespace t3 on t2.relnamespace=t3.oid "
                    "where t2.relkind in ($$t$$, $$r$$) "
                    "order by age(relfrozenxid) desc limit 5"
                )
                results = cursor.fetchall()
            if results:
                message_lines = []
                for row in results:
                    # row索引说明：0-当前数据库，1-角色名，2-命名空间，3-对象类型，4-对象名称，5-已使用年龄，6-剩余年龄
                    message_lines.append(f"表 '{row[4]}' 剩余年龄: {row[6]}")
                message = "\n".join(message_lines)
                return CheckItem(check_name=CHECK_NAME_TABLE_AGE,
                                 status=Status.SUCCESS.value,
                                 message=message)
            else:
                return CheckItem(check_name=CHECK_NAME_TABLE_AGE,
                                 status=Status.FAILURE.value,
                                 message="未查询到表剩余年龄数据")
        except Exception as e:
            return CheckItem(check_name=CHECK_NAME_TABLE_AGE,
                             status=Status.FAILURE.value,
                             message=f"表剩余年龄检查失败: {str(e)}")
