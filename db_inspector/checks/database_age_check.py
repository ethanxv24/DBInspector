from db_inspector.checks.base import BaseCheck, CheckItem, Status, manage_transaction

CHECK_NAME_DB_AGE = "数据库剩余年龄检查"

class PgDatabaseAgeCheck(BaseCheck):
    def run(self, db_connection):
        """
        查看数据库剩余年龄
        :param db_connection: PostgreSQL 数据库连接
        :return: CheckItem，包含检查结果
        """
        try:
            with manage_transaction(db_connection) as cursor:
                cursor.execute(
                    "select datname, age(datfrozenxid), 2^31 - age(datfrozenxid) as age_remain "
                    "from pg_database order by age(datfrozenxid) desc"
                )
                results = cursor.fetchall()
            if results:
                # 这里以剩余年龄最高的数据库作为示例返回信息
                top_db = results[0]
                message = f"数据库 '{top_db[0]}' 剩余年龄: {top_db[2]}"
                return CheckItem(check_name=CHECK_NAME_DB_AGE,
                                 status=Status.SUCCESS.value,
                                 message=message)
            else:
                return CheckItem(check_name=CHECK_NAME_DB_AGE,
                                 status=Status.FAILURE.value,
                                 message="未查询到数据库剩余年龄数据")
        except Exception as e:
            return CheckItem(check_name=CHECK_NAME_DB_AGE,
                             status=Status.FAILURE.value,
                             message=f"数据库剩余年龄检查失败: {str(e)}")
