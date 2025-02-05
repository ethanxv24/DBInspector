# import psycopg2
# import json
# from abc import ABC, abstractmethod
# from jinja2 import Template
#
# class PgPipeline(BasePipeline):
#     def get_check_methods(self):
#         return [
#             self.check_version,
#             self.check_connection_count,
#             self.check_replication_status
#         ]
#
#     def check_version(self):
#         """Check the PostgreSQL version."""
#         self.cursor.execute("SELECT version();")
#         version_info = self.cursor.fetchone()[0]
#         return {"pg_version": version_info}
#
#     def check_connection_count(self):
#         """Check the current connection count."""
#         self.cursor.execute("SELECT count(*) FROM pg_stat_activity;")
#         connection_count = self.cursor.fetchone()[0]
#         return {"connection_count": connection_count}
#
#     def check_replication_status(self):
#         """Check the replication status."""
#         self.cursor.execute("SELECT * FROM pg_stat_replication;")
#         replication_info = self.cursor.fetchall()
#         return {"replication_status": replication_info if replication_info else "No replication"}
import json
from urllib.parse import urlparse

import psycopg2

from db_inspector.checks.base import BaseCheck
from db_inspector.checks.connection_check import PgConnectionCheck
from db_inspector.checks.performance_check import PgPerformanceCheck
from db_inspector.checks.replication_check import PgReplicationCheck
from db_inspector.pipelines.base import PipelineManager

def run_pg_pipeline(db_connection):
    """
    执行 PostgreSQL 数据库的检查项管道
    :param db_connection: PostgreSQL 数据库连接对象
    :return: 所有检查项的结果列表
    """
    # 创建管道管理器
    pipeline = PipelineManager()

    # 创建 PostgreSQL 特有的检查项实例
    pg_connection_check = PgConnectionCheck()
    pg_replication_check = PgReplicationCheck()
    pg_performance_check = PgPerformanceCheck()

    # 将检查项添加到管道中
    pipeline.add_check(pg_connection_check)
    pipeline.add_check(pg_replication_check)
    pipeline.add_check(pg_performance_check)

    # 执行管道，获取检查结果
    results = pipeline.execute(db_connection)

    # 返回所有检查结果
    return results


# 检查项名称到类的映射字典
CHECKS_MAP = {
    "connection_check": PgConnectionCheck,
    "replication_check": PgReplicationCheck,
    "performance_check": PgPerformanceCheck,
}

class PostgreSQLPipeline(PipelineManager):
    def __init__(self,db_params=None, db_uri=None,checks=None,check_names=None, report_format='json'):
        """
        初始化 PostgreSQL 检查管道
        :param db_params: 数据库连接参数（如 host、dbname、user、password）
        :param checks: 可选，检查项列表，默认为空，允许传入需要执行的检查项
        :param report_format: 报告格式，默认为 'json'
        """
        self.db_params = db_params
        self.db_connection = None
        self.db_uri = db_uri if db_uri else self.parse_db_uri()
        self.checks = checks if checks else []  # 如果没有传入检查项，则使用空列表
        self.check_names = check_names if check_names else []  # 如果没有传入检查项，则使用空列表
        self.report_format = report_format

    def parse_db_uri(self):
        """
        解析数据库连接串，提取数据库类型和连接参数
        """
        # 使用 urllib.parse 解析连接串
        parsed_uri = urlparse(self.db_uri)

        # 提取数据库类型（如 postgres, mysql）
        self.db_type = parsed_uri.scheme

        # 提取其他参数（如用户名、密码、主机、端口、数据库名）
        self.db_params = {
            'user': parsed_uri.username,
            'password': parsed_uri.password,
            'host': parsed_uri.hostname,
            'port': parsed_uri.port,
            'dbname': parsed_uri.path[1:],  # 去掉开头的 '/'
        }

        print(f"Database type: {self.db_type}")
        print(f"Database parameters: {self.db_params}")

        # # 根据数据库类型选择相应的连接方法
        # if self.db_type == "postgres":
        #     self.connect_postgresql()
        # elif self.db_type == "mysql":
        #     self.connect_mysql()
        # else:
        #     raise ValueError(f"Unsupported database type: {self.db_type}")

    def connect(self):
        """
        创建与 PostgreSQL 数据库的连接
        """
        try:
            self.db_connection = psycopg2.connect(**self.db_params)
            if  not self.db_connection:
                raise ValueError("Database connection is not established")

            print("Database connection successful")
        except Exception as e:
            print(f"Failed to connect to database: {e}")
            self.db_connection = None

    def add_check(self, check: BaseCheck):
        """
        添加检查项到管道
        :param check: 检查项对象，继承自 BaseCheck
        """
        if not isinstance(check, BaseCheck):
            raise ValueError("check must be an instance of BaseCheck or its subclass")
        self.checks.append(check)
    def set_checks(self):
        """
        根据传入的检查项名称列表，动态添加检查项到管道中
        :param check_names: 检查项名称列表（文本数组）
        """
        for check_name in self.check_names:
            if check_name in CHECKS_MAP:
                check_class = CHECKS_MAP[check_name]
                self.add_check(check_class())
            else:
                print(f"Warning: Check '{check_name}' not recognized")
    def execute(self):
        """
        执行所有检查项并返回结果
        :return: 所有检查项的结果列表
        """
        if not self.db_connection:
            raise ValueError("Database connection is not established")

        results = []
        for check in self.checks:
            result = check.run(self.db_connection)
            results.append(result)
        return results

    def generate_report(self, results):
        """
        根据检查结果生成报告
        :param results: 检查结果列表
        :return: 报告字符串
        """
        if self.report_format == 'json':
            return json.dumps(results, indent=4)
        elif self.report_format == 'html':
            # 简单生成 HTML 格式报告
            html_report = "<html><body><h1>PostgreSQL Check Report</h1><ul>"
            for result in results:
                html_report += f"<li>Status: {result['status']}, Message: {result['message']}</li>"
            html_report += "</ul></body></html>"
            return html_report
        else:
            raise ValueError("Unsupported report format")

    def close(self):
        """
        关闭数据库连接
        """
        if self.db_connection:
            self.db_connection.close()
            print("Database connection closed")
