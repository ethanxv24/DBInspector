from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from jinja2 import Template
from datetime import datetime
import os
import mysql.connector
from mysql.connector import Error

''' readme
    MongoDB Inspection Report
    
    1. 使用方法 python3 环境 安装特定依赖
        pip install jinja2==3.1.4 pymongo==4.11.3 mysql-connector-python
          pip install mysql-connector-python
    2. 设置数据库执行配置
        [CONFIG]配置
    3. 执行
        python3 ./mongodb_inspector.py
'''


'''
获取MongoDB版本信息
db.version()

获取数据库列表 及 大小，取top 5
show dbs

db.getCollectionNames().forEach(c => {
    const stats = db[c].stats();
    print(`${c}: 
      存储大小 = ${(stats.storageSize / 1024 / 1024).toFixed(2)} MB,
      数据大小 = ${(stats.size / 1024 / 1024).toFixed(2)} MB,
      索引大小 = ${(stats.totalIndexSize / 1024 / 1024).toFixed(2)} MB
    `);
});

节点角色状态：
var a = rs.status(); 
a.members.forEach(function(e){print(e.name, e.stateStr)})
    启动时长
    db.serverStatus().uptime
    
    数据库内存使用情况
    db.serverStatus().mem
    
    增删改查数量
    db.serverStatus().opcounters
    
    连接数
    db.serverStatus().connections


节点角色状态：
var a = rs.status(); 
a.members.forEach(function(e){print(e.name, e.stateStr)})
'''

# 详细报告模板
DETAIL_HTML_TEMPLATE= '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>MongoDB Inspection Report</title>
        <meta charset="UTF-8">
        <style>
            body {
                font-family: Arial, sans-serif;
            }
            h1 {
                color: #333;
            }
            h2 {
                color: #555;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }
            th, td {
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }
            th {
                background-color: #f2f2f2;
            }
            tr:hover {
                background-color: #ddd;
            }
            .summary-report {
                border: 2px solid #007BFF;
                padding: 20px;
                margin: 20px;
                border-radius: 5px;
            }
            .database-report {
                border: 2px solid #28a745;
                padding: 20px;
                margin: 20px;
                border-radius: 5px;
            }
            .links {
                margin-bottom: 20px;
            }
            .links a {
                margin-right: 10px;
            }
            .stats {
                margin-bottom: 20px;
            }
            .passed {
                color: green;
                background-color: #e6ffe6; /* 新增背景颜色 */
            }
            .failed {
                color: red;
                background-color: #ffe6e6; /* 新增背景颜色 */
            }
            .error {
                color: orange;
                background-color: #fff9db; /* 新增背景颜色 */
            }
        </style>
    </head>
    <body>
        <div class="database-report">
            <h1>MongoDB Inspection Report for {{ db_name }}</h1>
            <div class="links">
                <a href="summary_report.html">返回汇总页面</a>
            </div>
            <div class="stats">
                <p>总检查项数: {{ total_checks }} | 成功项数: <span class="passed">{{ passed_checks }}</span> | 错误项数: <span class="failed">{{ failed_checks }}</span> | 错误状态项数: <span class="error">{{ error_checks }}</span></p>
            </div>
            {% for check_group_name, results in results_by_group.items() %}
            <h2>{{ check_group_name }}</h2>
            <table border="1">
                <thead>
                    <tr>
                        <th>Check Item</th>
                        <th>Status</th>
                        <th>Actual Result</th>
                        <th>Expected Result</th>
                    </tr>
                </thead>
                <tbody>
                    {% for name, result in results.items() %}
                    <tr class="{{ result.status.lower() }}"> <!-- 根据状态添加类 -->
                        <td>{{ name }}</td>
                        <td>{{ result.status }}</td>
                        <td><pre>{{ result.actual_result }}</pre></td> <!-- 使用 <pre> 标签保留格式 -->
                        <td>{{ result.expected_result }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% endfor %}
        </div>
    </body>
    </html>
'''

# 汇总报告模板
SUMMARY_HTML_TEMPLATE= '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>MongoDB Inspection Summary Report</title>
        <meta charset="UTF-8">
        <style>
            body {
                font-family: Arial, sans-serif;
            }
            h1 {
                color: #333;
            }
            h2 {
                color: #555;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }
            th, td {
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }
            th {
                background-color: #f2f2f2;
            }
            tr:hover {
                background-color: #ddd;
            }
            .summary-report {
                border: 2px solid #007BFF;
                padding: 20px;
                margin: 20px;
                border-radius: 5px;
            }
            .database-report {
                border: 2px solid #28a745;
                padding: 20px;
                margin: 20px;
                border-radius: 5px;
            }
            .links {
                margin-bottom: 20px;
            }
            .links a {
                margin-right: 10px;
            }
            .stats {
                margin-bottom: 20px;
            }
            .passed {
                color: green;
                background-color: #e6ffe6; /* 新增背景颜色 */
            }
            .failed {
                color: red;
                background-color: #ffe6e6; /* 新增背景颜色 */
            }
            .error {
                color: orange;
                background-color: #fff9db; /* 新增背景颜色 */
            }
        </style>
    </head>
    <body>
        <div class="summary-report">
            <h1>MongoDB Inspection Summary Report</h1>
            <div class="stats">
                <p>总检查项数: {{ total_checks }} | 成功项数: <span class="passed">{{ passed_checks }}</span> | 错误项数: <span class="failed">{{ failed_checks }}</span> | 错误状态项数: <span class="error">{{ error_checks }}</span></p>  <!-- 新增显示Error项数 -->
            </div>
            {% for db_config in config['databases'] %}
            <div class="database-report">
                <h2>{{ db_config['name'] }}</h2>
                <div class="links">
                    <a href="{{ db_links[db_config['name']] }}">查看详细报告</a>
                </div>
                <div class="stats">
                    {% set db_results = db_results[db_config['name']].items() %}
                    {% set db_total_checks = db_results|length %}
                    {% set db_passed_checks = db_results|selectattr('1.status', 'equalto', 'Passed')|list|length %}
                    {% set db_failed_checks = db_results|selectattr('1.status', 'equalto', 'Failed')|list|length %}
                    {% set db_error_checks = db_results|selectattr('1.status', 'equalto', 'Error')|list|length %}
                    <p>总检查项数: {{ db_total_checks }} | 成功项数: <span class="passed">{{ db_passed_checks }}</span> | 错误项数: <span class="failed">{{ db_failed_checks }}</span> | 错误状态项数: <span class="error">{{ db_error_checks }}</span></p>
                </div>
                {% if db_error_checks > 0 %}
                <h3>错误检查项详情</h3>
                <table border="1">
                    <tr>
                        <th>Check Group</th>
                        <th>Check Item</th>
                        <th>Status</th>
                        <th>Actual Result</th>
                        <th>Expected Result</th>
                    </tr>
                    {% for name,result in db_results if result.status == 'Error' %}
                    <tr>
                        <td>{{ result.check_group }}</td>
                        <td>{{ result.name }}</td>
                        <td>{{ result.status }}</td>
                        <td><pre>{{ result.actual_result }}</pre></td> <!-- 使用 <pre> 标签保留格式 -->
                        <td>{{ result.expected_result }}</td>
                    </tr>
                    {% endfor %}
                </table>
                {% endif %}
            </div>
            {% endfor %}
        </div>
    </body>
    </html>
'''

# 定义检查项类
class CheckItem:
    # 定义检查项名称到方法名的映射
    METHOD_MAP = {
        "MONGODB_VERSION_CHECK": "check_mongodb_version",
        "TOP_5_DATABASES_SIZE_CHECK": "check_top_5_databases_size",
        "COLLECTION_STATS_CHECK": "check_collection_stats",
        "SERVER_UPTIME_CHECK": "check_server_uptime",
        "MEMORY_USAGE_CHECK": "check_memory_usage",
        "OPCOUNTERS_CHECK": "check_opcounters",
        "CONNECTIONS_CHECK": "check_connections"
    }

    def __init__(self, name, expected_value, check_type, exec_func, remark, is_cloud_check=None):
        self.name = name
        self.remark = remark
        self.exec_func = self.METHOD_MAP.get(exec_func)
        self.expected_value = expected_value
        self.check_type = check_type
        self.is_cloud_check = is_cloud_check  # 是否云数据库的检查项 None: 云和非云数据库都需要的检查项 True: 云数据库检查项 False: 非云数据库检查项

    def execute(self, client, db_name, check_group):
        try:
            method = getattr(self, self.exec_func)
            actual_result = method(client)

            # 根据检查类型判断结果
            if self.check_type == 'output_contains':
                status = 'Passed' if self.expected_value in str(actual_result) else 'Failed'
            elif self.check_type == 'threshold':
                actual_value = float(actual_result)
                expected_value = float(self.expected_value)
                # if comparison == 'greater_than':
                #     status = 'Passed' if actual_value > expected_value else 'Failed'
                # else:
                #     status = 'Failed'
            else:
                status = 'Failed'

            # 记录结果
            return {
                'name': self.name,
                'db_name': db_name,
                'check_group': check_group,
                'status': status,
                'actual_result': actual_result,
                'expected_result': self.expected_value
            }
        except Exception as e:
            return {
                'name': self.name,
                'db_name': db_name,
                'check_group': check_group,
                'status': 'Error',
                'actual_result': str(e),
                'expected_result': self.expected_value
            }

    def check_mongodb_version(self, client):
        # 检查 MongoDB 服务器的版本
        return client.admin.command('serverStatus')['version']

    def check_top_5_databases_size(self, client):
        # 检查前 5 大数据库的大小
        databases = client.list_database_names()
        database_sizes = []
        for db_name in databases:
            db = client[db_name]
            total_storage_size = 0
            total_data_size = 0
            total_index_size = 0
            for c in db.list_collection_names():
                stats = db.command("collstats", c)
                total_storage_size += stats.get('storageSize', 0)
                total_data_size += stats.get('size', 0)
                total_index_size += stats.get('totalIndexSize', 0)
            database_sizes.append({
                'name': db_name,
                '存储大小': total_storage_size / 1024 / 1024,
                '数据大小': total_data_size / 1024 / 1024,
                '索引大小': total_index_size / 1024 / 1024
            })
        sorted_databases = sorted(database_sizes, key=lambda x: x['数据大小'], reverse=True)
        return sorted_databases[:5]

    def check_collection_stats(self, client):
        # 检查每个集合的存储、数据和索引大小
        # 执行 rs.status() 命令
        rs_status = client.admin.command('replSetGetStatus')

        # 遍历成员列表
        db_stats = []
        for member in rs_status.get('members', []):
            name = member.get('name')
            state_str = member.get('stateStr')
            print(name, state_str)
            db_stats.append({ 'name': member.get('name'), 'stats':  member.get('stateStr') })
        return db_stats

    def check_server_uptime(self, client):
        # 检查 MongoDB 服务器的运行时间
        return client.admin.command('serverStatus')['uptime']

    def check_memory_usage(self, client):
        # 检查 MongoDB 服务器的内存使用情况
        return client.admin.command('serverStatus')['mem']

    def check_opcounters(self, client):
        # 检查执行的操作数量（插入、查询、更新、删除、命令）
        return client.admin.command('serverStatus')['opcounters']

    def check_connections(self, client):
        # 检查当前连接到 MongoDB 服务器的连接数
        return client.admin.command('serverStatus')['connections']

# 定义检查组类
class CheckGroup:
    def __init__(self, name, remark, checks):
        self.name = name
        self.remark = remark
        self.checks = checks

    def perform_checks(self, db_name, client):
        results = {}
        for check in self.checks:
            result = check.execute(client, db_name, self.name)
            results[f"{check.name}"] = result
        return results

# 执行检查
def perform_checks(db_name, client, check_groups, checks_to_run, is_cloud):
    results_by_group = {}
    for check_group_name, check_group in check_groups.items():
        if check_group_name in checks_to_run:
            group_results = {}
            for check in check_group.checks:
                if (check.is_cloud_check is None) or \
                   (check.is_cloud_check and is_cloud) or \
                   (not check.is_cloud_check and not is_cloud):
                    result = check.execute(client, db_name, check_group_name)
                    group_results[f"{check.name}"] = result
            results_by_group[check_group_name] = group_results
    return results_by_group

# 定义格式化 JSON 结果的函数
def format_result(result):
    import json
    try:
        formatted_result = json.dumps(result,ensure_ascii=False, indent=4)
    except (TypeError, json.JSONDecodeError):
        formatted_result = result

    return formatted_result

# 生成详细HTML报告
def generate_html_report(results_by_group, output_path, db_name):
    print(f"    正在为 {db_name} 生成详细报告，路径为 {output_path}")  # 修改为中文
    # 统计成功项数、错误项数以及总项数
    total_checks = sum(len(results) for results in results_by_group.values())
    passed_checks = sum(1 for results in results_by_group.values() for result in results.values() if result['status'] == 'Passed')
    failed_checks = sum(1 for results in results_by_group.values() for result in results.values() if result['status'] == 'Failed')
    error_checks = sum(1 for results in results_by_group.values() for result in results.values() if result['status'] == 'Error')

    # 格式化实际结果
    for group_results in results_by_group.values():
        for result in group_results.values():
            result['actual_result'] = format_result(result['actual_result'])

    # 过滤掉没有检查项的检查组
    filtered_results_by_group = {k: v for k, v in results_by_group.items() if v}

    template = Template(DETAIL_HTML_TEMPLATE)
    html_content = template.render(results_by_group=filtered_results_by_group, db_name=db_name, total_checks=total_checks, passed_checks=passed_checks, failed_checks=failed_checks, error_checks=error_checks)
    with open(output_path, 'w', encoding='utf-8') as file:
        file.write(html_content)

# 生成汇总HTML报告
def generate_summary_html_report(results, output_path, config):
    print(f"    正在生成汇总报告，路径为 {output_path}")

    # 获取数据库名和文件相对地址链接
    db_links = {db_config['name']: f"{db_config['name'].replace(' ', '_')}_report.html" for db_config in config['databases']}

    # 修正总检查项数统计方式
    total_checks = len([r for r in results if r[1]['status'] in ['Passed', 'Failed', 'Error']])

    # 统计成功项数、错误项数以及总项数
    passed_checks = sum(1 for k, result in results if result['status'] == 'Passed')
    failed_checks = sum(1 for k, result in results if result['status'] == 'Failed')
    error_checks = sum(1 for k, result in results if result['status'] == 'Error')  # 新增统计Error项数

    # 按数据库分组统计
    db_results = {}
    for db_config in config['databases']:
        db_name = db_config['name']
        db_results[db_name] = {f'{name}_{result["check_group"]}': result for name, result in results if db_name == result['db_name']}

    # 格式化实际结果
    for db_name, results in db_results.items():
        for result in results.values():
            result['actual_result'] = format_result(result['actual_result'])

    # 过滤掉没有检查项的数据库结果
    filtered_db_results = {k: v for k, v in db_results.items() if v}

    template = Template(SUMMARY_HTML_TEMPLATE)
    html_content = template.render(results=results, db_links=db_links, total_checks=total_checks, passed_checks=passed_checks, failed_checks=failed_checks, error_checks=error_checks, config=config, db_results=filtered_db_results)  # 更新模板渲染参数
    with open(output_path, 'w', encoding='utf-8') as file:
        file.write(html_content)

# 主函数
def main():
    # 记录开始时间
    start_time = datetime.now()
    print(f"脚本开始执行时间: {start_time}")  # 新增输出开始时间

    # 加载配置文件
    config = CONFIG

    # 检查并创建输出目录
    output_report_dir = CONFIG['outputReportDir']

    # 获取当前时间并创建一个新的子目录
    current_date = start_time.strftime("reports_%Y%m%d%H%M%S")
    new_output_report_dir = os.path.join(output_report_dir, current_date)

    if not os.path.exists(new_output_report_dir):
        os.makedirs(new_output_report_dir)
        print(f"    已创建新的输出报告目录: {new_output_report_dir}")  # 修改为中文
    else:
        print(f"    输出报告目录已存在: {new_output_report_dir}")  # 修改为中文

    all_results = []

    for db_config in config['databases']:
        uri = db_config['uri']
        db_name = db_config['name']
        is_cloud = db_config['is_cloud']  # 获取是否为云数据库的配置

        checks_to_run = check_groups.keys()
        with MongoClient(uri, server_api=ServerApi('1')) as client:
            db_results_by_group = perform_checks(db_name, client, check_groups, checks_to_run, is_cloud)

        # 生成每个数据库的详细报告
        db_report_path = os.path.join(new_output_report_dir, f'{db_name.replace(" ", "_")}_report.html')
        generate_html_report(db_results_by_group, db_report_path, db_name)

        # 汇总结果
        for group_results in db_results_by_group.values():
            all_results.extend(group_results.items())

    # 生成汇总报告
    generate_summary_html_report(all_results, os.path.join(new_output_report_dir, 'summary_report.html'), config)

    # 记录结束时间
    end_time = datetime.now()
    execution_time = end_time - start_time
    print(f"脚本执行结束,结束时间:{end_time},总耗时: {execution_time}")

# 初始化检查组
check_groups = {
    "database_performance":  CheckGroup("数据库性能", "与数据库性能和配置相关的检查。",[
        CheckItem("MongoDB 版本检查", "", "output_contains","MONGODB_VERSION_CHECK","检查 MongoDB 服务器的版本。", None),
        CheckItem("前 5 大数据库大小检查", "", "output_contains","TOP_5_DATABASES_SIZE_CHECK","检查前 5 大数据库的大小。", None),
        CheckItem("集合统计信息检查",  "", "output_contains","COLLECTION_STATS_CHECK","检查每个集合的存储、数据和索引大小。", None),
        CheckItem("服务器运行时间检查", "", "output_contains","SERVER_UPTIME_CHECK","检查 MongoDB 服务器的运行时间。", None),
        CheckItem("内存使用情况检查",  "", "output_contains","MEMORY_USAGE_CHECK","检查 MongoDB 服务器的内存使用情况。", None),
        CheckItem("操作计数器检查",  "", "output_contains","OPCOUNTERS_CHECK","检查执行的操作数量（插入、查询、更新、删除、命令）。", None),
        CheckItem("连接数检查", "", "output_contains","CONNECTIONS_CHECK","检查当前连接到 MongoDB 服务器的连接数。", False)
    ]),
    "database_performance2": CheckGroup("数据库性能2", "与数据库性能和配置相关的检查。", [
        CheckItem("操作计数器检查", "", "output_contains","OPCOUNTERS_CHECK","检查执行的操作数量（插入、查询、更新、删除、命令）。", True),
        CheckItem("连接数检查",  "", "output_contains","CONNECTIONS_CHECK","检查当前连接到 MongoDB 服务器的连接数。", True)
    ])
}

# 添加配置
CONFIG = {
    'outputReportDir': './reports/',
    'databases': [
        {
            'name': "A数据库",
            'uri': "mongodb://127.0.0.1:27017",
            'is_cloud': False  # 是否云数据库
        },
        {
            'name': "B数据库",
            'uri': "mongodb://127.0.0.1:27017",
            'is_cloud': True
        }
    ]
}

if __name__ == '__main__':
    main()
