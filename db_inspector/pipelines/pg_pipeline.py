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
import os
from typing import List
from urllib.parse import urlparse

from dataclasses import asdict

import psycopg2

from db_inspector.checks.base import BaseCheck, Status
from db_inspector.checks.check_run import SQLCheck, ShellCheck
from db_inspector.checks.constant import get_check_config
from db_inspector.config.base import Check

from db_inspector.pipelines.base import PipelineManager
from db_inspector.reports.html_report import HTMLReportGenerator

class PostgreSQLPipeline(PipelineManager):
    def __init__(self,db_name=None,checks_conf:List[Check]=None,db_params=None, db_uri=None,checks=None,check_names=None, report_format='json',report_dir='report'):
        """
        初始化 PostgreSQL 检查管道
        :param db_params: 数据库连接参数（如 host、dbname、user、password）
        :param checks: 可选，检查项列表，默认为空，允许传入需要执行的检查项
        :param report_format: 报告格式，默认为 'json'
        """
        self.db_name = db_name
        self.db_params = db_params
        self.db_connection = None
        self.db_uri = db_uri if db_uri else self.parse_db_uri()
        self.checks = checks if checks else []  # 如果没有传入检查项，则使用空列表
        self.checks_conf = checks_conf if checks_conf else []  # 如果没有传入检查项，则使用空列表
        self.check_names = check_names if check_names else []  # 如果没有传入检查项，则使用空列表
        self.report_format = report_format
        self.report_dir = report_dir

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

    @property
    def execute(self):
        """
        执行所有检查项并返回结果
        :return: 所有检查项的结果列表
        """
        if not self.db_connection:
            raise ValueError("Database connection is not established")

        check_results = []
        for check in self.checks:
            result = check.run(self.db_connection)
            check_results.append(result)

        # 循环所有的检查项，将检查结果添加到列表中
        for check_conf in self.checks_conf:

            # 检查检查项配置是否为空
            if check_conf is None or check_conf.checks is None or len(check_conf.checks) == 0:
                continue

            # 读取检查项配置文件
            current_check_config = get_check_config()

            print(f"current_check_config:{current_check_config}")

            if current_check_config is None or current_check_config.check_groups is None or len(current_check_config.check_groups) == 0:
                print("Failed to load check configuration. Exiting...")
                return

            print(f"current_check_config.check_groups:{current_check_config.check_groups}")

            if current_check_config.check_groups.get(check_conf.group) is None:
                print(f"Check group '{check_conf.group}' not found in configuration")
                continue


            for check in check_conf.checks:
                if current_check_config.check_groups[check_conf.group].checks[check] is None:
                    print(f"Check '{check}' not found in group '{check_conf.group}'")
                    continue

                # TODO 执行配置
                check_item = current_check_config.check_groups[check_conf.group].checks[check]

                if check_item.type == "sql":
                    # 创建一个 SQL 检查对象
                    sql_check = SQLCheck(
                        query=check_item.query,
                        expected_value=check_item.expected_value,
                        comparison=check_item.comparison,
                        check_name=check_item.name
                    )
                    # 执行 SQL 检查
                    result = sql_check.run(self.db_connection)
                    check_results.append(result)
                elif check_item.type == "shell":
                    # 创建一个 Shell 检查对象
                    shell_check = ShellCheck(
                        command=check_item.command,
                        expected_value=check_item.expected_value,
                        check_name=check_item.name
                    )
                    # 执行 Shell 检查
                    result = shell_check.run()
                    check_results.append(result)
                else:
                    print(f"Warning: Check '{check}' not recognized")
            #
            # check_name = check_conf.name
            # check_params = check_conf.params
            # if check_name in CHECKS_MAP:
            #     check_class = CHECKS_MAP[check_name]
            #     check_instance = check_class(**check_params)
            #     result = check_instance.run(self.db_connection)
            #     check_results.append(result)
            # else:
            #     print(f"Warning: Check '{check_name}' not recognized")



        # 检查check_result 的正确错误的数量
        successCnt, failureCnt,warningCnt= 0,0,0
        for result in check_results:
            if result.status == Status.SUCCESS.value:
                successCnt += 1
            elif result.status == Status.FAILURE.value:
                failureCnt += 1
            elif result.status == Status.WARNING.value:
                warningCnt += 1

        results = {
            "db_name": self.db_name,
            "check_results": check_results,
            "success_count": successCnt,
            "failure_count": failureCnt,
            "warning_count": warningCnt,
            "report_link":f"{self.db_name}_report.html",
        },

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
            report_generator = HTMLReportGenerator()
            # 生成 HTML 报告并写入到文件 report.html
            html_report = report_generator.generate(results, output_file=os.path.join(self.report_dir, f"{self.db_name}_report.html"))
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
