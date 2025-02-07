from db_inspector.checks.base import BaseCheck, CheckItem, Status, manage_transaction

CHECK_NAME_ARCHIVE = "归档配置检查"

class PgArchiveConfigCheck(BaseCheck):
    def run(self, db_connection):
        """
        查看数据库是否开启归档，且归档参数已配置/可用
        :param db_connection: PostgreSQL 数据库连接
        :return: CheckItem，包含检查结果
        """
        try:
            with manage_transaction(db_connection) as cursor:
                cursor.execute("SELECT name, setting FROM pg_settings WHERE name IN ('archive_mode','archive_command')")
                settings = cursor.fetchall()
            # 将结果转换为字典，便于后续判断
            settings_dict = {row[0]: row[1] for row in settings}
            archive_mode = settings_dict.get('archive_mode', '').lower()
            archive_command = settings_dict.get('archive_command', '')
            if archive_mode == 'on' and archive_command and archive_command.lower() != 'disabled':
                return CheckItem(check_name=CHECK_NAME_ARCHIVE,
                                 status=Status.SUCCESS.value,
                                 message="归档已启用并正确配置")
            else:
                return CheckItem(check_name=CHECK_NAME_ARCHIVE,
                                 status=Status.FAILURE.value,
                                 message="归档未启用或配置不正确")
        except Exception as e:
            return CheckItem(check_name=CHECK_NAME_ARCHIVE,
                             status=Status.FAILURE.value,
                             message=f"归档配置检查失败: {str(e)}")
