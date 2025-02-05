from db_inspector.checks.base import BaseCheck


class PipelineManager:
    def __init__(self):
        # 初始化一个空列表，用于存储添加的检查项
        self.checks = []

    def add_check(self, check: BaseCheck):
        """
        将检查项添加到管道中
        :param check: 检查项对象，继承自 BaseCheck
        """
        if not isinstance(check, BaseCheck):
            raise ValueError("check must be an instance of BaseCheck or its subclass")
        self.checks.append(check)

    def execute(self, db_connection):
        """
        执行管道中的所有检查项
        :param db_connection: 数据库连接对象
        :return: 检查结果列表
        """
        results = []
        for check in self.checks:
            result = check.run(db_connection)  # 执行检查项
            results.append(result)  # 将检查结果添加到列表
        return results
