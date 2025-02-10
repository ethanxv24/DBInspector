import subprocess

from db_inspector.checks.base import manage_transaction, BaseCheck, CheckItem, CheckItemResult, Status


# SQL 类型检查类
class SQLCheck(BaseCheck):
    def __init__(self, query: str, expected_value: str, comparison: str, check_name: str = "SQLCheck"):
        """
        :param query: SQL 查询语句
        :param expected_value: 预期值（用于比较）
        :param comparison: 比较方式，例如 "greater_than"、"less_than"、"equal_to"
        :param check_name: 检查项名称
        """
        self.query = query
        self.expected_value = expected_value
        self.comparison = comparison
        self.check_name = check_name

    def run(self, db_connection):
        """
        执行 SQL 查询检查，并根据比较结果返回 CheckItem。
        """
        with manage_transaction(db_connection) as cursor:
            cursor.execute(self.query)
            result = cursor.fetchone()

        # 检查查询是否返回了结果
        if result is None:
            return CheckItemResult(self.check_name, Status.FAILURE.value, "No results returned from query.")

        # 获取查询结果的第一个字段
        result_value = result[0]

        # 根据比较类型判断检查是否通过
        if self.comparison == "greater_than" and result_value > float(self.expected_value):
            status = "SUCCESS"
            message = f"Result {result_value} is greater than {self.expected_value}."
        elif self.comparison == "less_than" and result < float(self.expected_value):
            status = "SUCCESS"
            message = f"Result {result_value} is less than {self.expected_value}."
        elif self.comparison == "equal_to" and result_value == float(self.expected_value):
            status = "SUCCESS"
            message = f"Result {result_value} equals {self.expected_value}."
        else:
            status = "FAILURE"
            message = f"Result {result_value} doesn't meet the threshold {self.expected_value}."


        return CheckItemResult(self.check_name, status, message)

# Shell 命令检查类
class ShellCheck(BaseCheck):
    def __init__(self, command: str, expected_value: str, check_name: str = "ShellCheck"):
        """
        :param command: 待执行的 shell 命令
        :param expected_value: 预期值，用于判断输出中是否包含该值
        :param check_name: 检查项名称
        """
        self.command = command
        self.expected_value = expected_value
        self.check_name = check_name

    def run(self, db_connection=None):
        """
        执行 shell 命令检查，并根据输出判断检查是否通过。
        :param db_connection: 对于 shell 检查通常不需要数据库连接，因此可传 None
        """
        try:
            result = subprocess.run(self.command, shell=True, capture_output=True, text=True)
            if self.expected_value in result.stdout:
                status = "SUCCESS"
                message = result.stdout.strip()
            else:
                status = "FAILURE"
                message = f"Expected value '{self.expected_value}' not found in output."
        except subprocess.CalledProcessError as e:
            status = "FAILURE"
            message = f"Command failed with error {e}"
        return CheckItemResult(self.check_name, status, message)
