import os
import threading
from datetime import datetime
import mysql.connector
from mysql.connector import Error
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from jinja2 import Template

''' readme
    MongoDB Inspection Report
    
    1. 使用方法 python3 环境 安装特定依赖
        pip3 install jinja2==3.1.4 pymongo==4.11.3 mysql-connector-python==8.0.26
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

# Role mode 常量
RM_PRIMARY_REPLICASET = "Primary_ReplicaSet"
RM_MASTER_SHARDING = "Master_Sharding"
RM_PRIMARY_SHARDING = "Primary_Sharding"
RM_PRIMARY_SINGLE = "Primary_Single"


# 数据源sql
DBLINKS_SQL = '''select * from my_table;'''

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
            .auto-wrap {
                white-space: pre-wrap;
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
    <h1>MongoDB Inspection Report for {{ db_links[0].instance_name }}</h1>
        <div class="stats">
            <p>总检查项数: {{ total_checks }} | 成功项数: <span class="passed">{{ passed_checks }}</span> | 错误项数: <span class="failed">{{ failed_checks }}</span> | 错误状态项数: <span class="error">{{ error_checks }}</span></p>  <!-- 新增显示Error项数 -->
        </div>
        <div class="links">
                <a href="summary_report.html">返回汇总页面</a>
            </div>
        {% for db_link in db_links %}
        <div class="database-report">
            <h2>Env: {{ db_link.environment }} | Role_Mode: {{db_link.role_mode}} | Node_Group_Name: {{db_link.node_group_name}}</h2>
            <div class="stats">
                <p>总检查项数: {{ checks_map[db_link.instance_name_env]['total_checks'] }} | 成功项数: <span class="passed">{{ checks_map[db_link.instance_name_env]['passed_checks'] }}</span> | 错误项数: <span class="failed">{{ checks_map[db_link.instance_name_env]['failed_checks'] }}</span> | 错误状态项数: <span class="error">{{ checks_map[db_link.instance_name_env]['error_checks'] }}</span></p>
            </div>
            {% for check_group_name, results in checks_map[db_link.instance_name_env]['filtered_results_by_group'].items() %}
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
                        <td><pre class="auto-wrap">{{ result.actual_result }}</pre></td> <!-- 使用 <pre> 标签保留格式 -->
                        <td>{{ result.expected_result }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% endfor %}
        </div>
        {% endfor %}
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
            .auto-wrap {
                white-space: pre-wrap;
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
            {% for k,db_links in db_link_maps.items() %}
                {% for db_link in db_links %}
                <div class="database-report">
                    <h2>{{ db_link.instance_name }}</h2>
                    <div class="stats">
                        <p>Env: {{ db_link.environment }} | Role_Mode: {{db_link.role_mode}} | Node_Group_Name: {{db_link.node_group_name}}</p>
                    </div>
                    <div class="links">
                        <a href="{{ report_links[db_link.instance_name] }}">查看详细报告</a>
                    </div>
                    <div class="stats">
                        {% set db_results = db_results[db_link.instance_name_env].items() %}
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
                            <td><pre class="auto-wrap">{{ result.actual_result }}</pre></td> <!-- 使用 <pre> 标签保留格式 -->
                            <td>{{ result.expected_result }}</td>
                        </tr>
                        {% endfor %}
                    </table>
                    {% endif %}
                </div>
                {% endfor %}
            {% endfor %}
        </div>
    </body>
    </html>
'''

# 定义数据库连接结构体类
class DatabaseLink:
    def __init__(self,id,  instance_name, environment, role_mode,node_group_name, data_path):
        self.id = id
        self.instance_name_env = id+"_"+instance_name+"_"+environment
        self.instance_name = instance_name
        self.environment = environment
        self.role_mode = role_mode
        self.node_group_name = node_group_name
        self.data_path = data_path

    def __str__(self):
        return f"ID: {self.id}, Instance Name: {self.instance_name}, Environment: {self.environment}, Role Mode: {self.role_mode}, Node Group Name: {self.node_group_name}, Data Path: {self.data_path}"

    def id(self):
        return self.id
    def instance_name_env(self):
        return self.instance_name_env
    def instance_name(self):
        return self.instance_name
    def environment(self):
        return self.environment
    def role_mode(self):
        return self.role_mode
    def node_group_name(self):
        return self.node_group_name
    def data_path(self):
        return self.data_path

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

    def __init__(self, name, expected_value, check_type, exec_func, remark, role_mode=None):
        self.name = name
        self.remark = remark
        self.exec_func = self.METHOD_MAP.get(exec_func)
        self.expected_value = expected_value
        self.check_type = check_type
        self.role_mode = role_mode  # 运行模式 Primary_Sharding:分片节点 Primary_ReplicaSet:主从，三个节点 Primary_Single:归档节点 Master_Sharding:mongos节点

    def execute(self, client, db_link, check_group):
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
                'db_name': db_link.instance_name,
                'environment':db_link.environment,
                'instance_name_env':db_link.instance_name_env,
                'role_mode':db_link.role_mode,
                'node_group_name':db_link.node_group_name,
                'data_path':db_link.data_path,
                'check_group': check_group,
                'status': status,
                'actual_result': actual_result,
                'expected_result': self.expected_value
            }
        except Exception as e:
            return {
                'name': self.name,
                'db_name': db_link.instance_name,
                'environment':db_link.environment,
                'instance_name_env':db_link.instance_name_env,
                'role_mode':db_link.role_mode,
                'node_group_name':db_link.node_group_name,
                'data_path':db_link.data_path,
                'check_group': check_group,
                'status': 'Error',
                'actual_result': str(e),
                'expected_result': self.expected_value
            }

    def check_mongodb_version(self, client):
        try:
            # 检查 MongoDB 服务器的版本
            # 执行 serverStatus 命令并获取版本信息
            server_status = client.admin.command('serverStatus')
            version = server_status['version']
            return version
        except Exception as e:
            print(f"--------发生错误: {e} [check_mongodb_version] ")

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
def perform_checks(db_link, client, check_groups, checks_to_run):
    results_by_group = {}
    for check_group_name, check_group in check_groups.items():
        if check_group_name in checks_to_run:
            group_results = {}
            for check in check_group.checks:
                if (check.role_mode is None) or \
                   (check.role_mode ==db_link.role_mode):
                    check_item_start_time = datetime.now()
                    result = check.execute(client, db_link, check_group_name)

                   # 记录日志
                    check_item_end_time = datetime.now()
                    check_item_execution_time = check_item_end_time - check_item_start_time
                    # 如果判断执行时长 分别对超过2s、5s、20s 的情况进行不同程度的日志输出
                    if check_item_execution_time.total_seconds() > 20:
                        print(f"--------[!!!]执行时间超过20s,耗时:[{check_item_execution_time}],detail:[{db_link.instance_name_env}] | [{db_link.role_mode}] | [{check_group_name}] | [{check.name}]")
                    elif check_item_execution_time.total_seconds() > 5:
                        print(f"--------[!!]执行时间超过5s,耗时:[{check_item_execution_time}],detail:[{db_link.instance_name_env}] | [{db_link.role_mode}] | [{check_group_name}] | [{check.name}]")
                    elif check_item_execution_time.total_seconds() > 2:
                        print(f"--------[!]执行时间超过2s,耗时:[{check_item_execution_time}],detail:[{db_link.instance_name_env}] | [{db_link.role_mode}] | [{check_group_name}] | [{check.name}]")

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
def generate_html_report(db_results, output_path, db_links):
    print(f"----正在为 [{db_links[0].instance_name}] 生成详细报告，路径为:[{output_path}]")  # 修改为中文

    checks_map ={}
    total_checks,passed_checks,failed_checks,error_checks = 0,0,0,0

    for instance_name_env,db_result in db_results.items():
        # 统计成功项数、错误项数以及总项数
        checks_map[instance_name_env] = {
            'total_checks': sum(len(group_results) for group_results in db_result.values()),
            'passed_checks': sum(1 for group_results in db_result.values() for result in group_results.values() if result['status'] == 'Passed'),
            'failed_checks': sum(1 for group_results in db_result.values() for result in group_results.values() if result['status'] == 'Failed'),
            'error_checks': sum(1 for group_results in db_result.values() for result in group_results.values() if result['status'] == 'Error')
        }

        # # 统计成功项数、错误项数以及总项数
        # checks_map[instance_name_env]['total_checks'] = sum(len(results) for results in db_result.values())
        # checks_map[instance_name_env]['passed_checks'] = sum(1 for results in db_result.values() for result in results.values() if result['status'] == 'Passed')
        # checks_map[instance_name_env]['failed_checks']  = sum(1 for results in db_result.values() for result in results.values() if result['status'] == 'Failed')
        # checks_map[instance_name_env]['error_checks']  = sum(1 for results in db_result.values() for result in results.values() if result['status'] == 'Error')
        #


        # 格式化实际结果
        for group_results in db_result.values():
            for result in group_results.values():
                result['actual_result'] = format_result(result['actual_result'])

        # 过滤掉没有检查项的检查组
        checks_map[instance_name_env]['filtered_results_by_group'] = {k: v for k, v in db_result.items() if v}

        for  instance_name_env,stats in checks_map.items():
            total_checks += stats['total_checks']
            passed_checks += stats['passed_checks']
            failed_checks += stats['failed_checks']
            error_checks += stats['error_checks']

    template = Template(DETAIL_HTML_TEMPLATE)
    html_content = template.render(checks_map=checks_map, db_links=db_links, total_checks=total_checks, passed_checks=passed_checks, failed_checks=failed_checks, error_checks=error_checks)
    with open(output_path, 'w', encoding='utf-8') as file:
        file.write(html_content)

# 生成汇总HTML报告
def generate_summary_html_report(results, output_path):
    print(f"----正在生成汇总报告，路径为:[{output_path}]")

    # 获取数据库名和文件相对地址链接
    report_links = {k:f"{k.replace(' ', '_')}_report.html" for k,db_link in db_link_maps.items()}

    # 修正总检查项数统计方式
    total_checks = len([r for r in results if r[1]['status'] in ['Passed', 'Failed', 'Error']])

    # 统计成功项数、错误项数以及总项数
    passed_checks = sum(1 for k, result in results if result['status'] == 'Passed')
    failed_checks = sum(1 for k, result in results if result['status'] == 'Failed')
    error_checks = sum(1 for k, result in results if result['status'] == 'Error')  # 新增统计Error项数

    # 按数据库分组统计
    db_results = {}
    for k,db_links in db_link_maps.items():
        for db_link in db_links:
            db_results[db_link.instance_name_env] = {
                f'{name}_{result["check_group"]}': result
                for name, result in results
                if db_link.instance_name_env == result['instance_name_env']
            }
            #db_results[v.instance_name_env] = {f'{name}_{result["check_group"]}': result for name, result in results if v.instance_name_env == result['instance_name_env']}

    # 格式化实际结果
    for db_name, results in db_results.items():
        for result in results.values():
            result['actual_result'] = format_result(result['actual_result'])

    # 过滤掉没有检查项的数据库结果
    filtered_db_results = {k: v for k, v in db_results.items() if v}

    template = Template(SUMMARY_HTML_TEMPLATE)
    html_content = template.render(results=results, report_links=report_links, total_checks=total_checks, passed_checks=passed_checks, failed_checks=failed_checks, error_checks=error_checks, db_link_maps=db_link_maps, db_results=filtered_db_results)  # 更新模板渲染参数
    with open(output_path, 'w', encoding='utf-8') as file:
        file.write(html_content)

# 获取数据库链接数据
def fetch_db_link_data():
    try:
        # 从配置中提取MySQL URL
        mysql_url = CONFIG.get('dblink_source', '')

        print(f"--正在从mysql库查询MongoDB巡检数据，url为: [{mysql_url}], 查询sql为: [{DBLINKS_SQL}]")

        if not mysql_url.startswith("mysql://"):
            raise ValueError("Invalid MySQL URL format")

        # 去掉前缀并解析URL
        mysql_url = mysql_url[len("mysql://"):]
        if '@' not in mysql_url or '/' not in mysql_url:
            raise ValueError("Malformed MySQL URL")

        user_password, host_db = mysql_url.split('@', 1)
        user, password = user_password.split(':', 1)
        host, database = host_db.split('/', 1)
        domain, port = host.split(':', 1)

        # 数据库连接参数
        db_config = {
            'host': domain,
            'database': database,
            'user': user,
            'password': password
        }

        # 使用上下文管理器管理数据库连接和游标
        with mysql.connector.connect(**db_config) as connection:
            if not connection.is_connected():
                raise ConnectionError("Failed to connect to the database")

            with connection.cursor(dictionary=True) as cursor:
                # 执行SQL查询
                cursor.execute(DBLINKS_SQL)
                rows = cursor.fetchall()
                for index, row in enumerate(rows):
                #for row in rows:
                    table_obj = DatabaseLink(str(index),row['instance_name'], row['environment'], row['role_mode'], row['node_group_name'],row['data_path'])
                    #db_links.append(table_obj)

                    # 将 DatabaseLink 对象添加到 db_link_maps 中，根据 instance_name 分组
                    instance_name = row['instance_name']
                    if instance_name not in db_link_maps:
                        db_link_maps[instance_name] = []
                    db_link_maps[instance_name].append(table_obj)

                # 调试模式下打印结果
                #print(f"Rows:{rows}")

    except (ValueError, KeyError, AttributeError) as e:
        print(f"--Configuration Error: {e}")
    except Error as e:
        print(f"--MySQL Error: {e}")
    except Exception as e:
        print(f"--Unexpected Error: {e}")
    finally:
        print(f"--mysql数据库巡检数据查询完成,从mysql库查询到MongoDB巡检数据，共 [{len(rows)}] 条数据")

#全局数据集
all_results = []
# 线程锁，用于线程安全
lock = threading.Lock()

# 主函数
def main():
    # 记录开始时间
    start_time = datetime.now()
    print(f"脚本开始执行时间: [{start_time}]")  # 新增输出开始时间

    # 获取数据库链接数据
    fetch_db_link_data()

    if not db_link_maps:
        print("--No database links found. Exiting...")
        return

    # 检查并创建输出目录
    output_report_dir = CONFIG['outputReportDir']

    # 获取当前时间并创建一个新的子目录
    current_date = start_time.strftime("reports_%Y%m%d%H%M%S")
    new_output_report_dir = os.path.join(output_report_dir, current_date)

    if not os.path.exists(new_output_report_dir):
        os.makedirs(new_output_report_dir)
        print(f"----已创建新的输出报告目录: [{new_output_report_dir}]")  # 修改为中文
    else:
        print(f"----输出报告目录已存在: [{new_output_report_dir}]")  # 修改为中文


    #加载所有检查项
    checks_to_run = check_groups.keys()

    # 任务列表
    threads = []
    # 创建一个信号量对象，最大并发数为 4
    semaphore = threading.Semaphore(CONFIG['max_threads'])

    def worker(db_links,checks_to_run):
        global all_results
        # 获取信号量，如果达到最大并发数，线程会阻塞
        with semaphore:

            if len(db_links) == 0:
                print("--No database links found. Exiting...")
                return

            db_results = {}

            for db_link in db_links:
                # 模拟数据处理
                with MongoClient(db_link.data_path, server_api=ServerApi('1')) as client:
                    db_results_by_group = perform_checks(db_link, client, check_groups, checks_to_run)
                    db_results[db_link.instance_name_env] = db_results_by_group

                with lock:
                    # 汇总结果
                    for group_results in db_results_by_group.values():
                        all_results.extend(group_results.items())
                    #results.append(result)

            # 生成每个数据库的详细报告
            db_report_path = os.path.join(new_output_report_dir, f'{db_links[0].instance_name.replace(" ", "_")}_report.html')
            generate_html_report(db_results, db_report_path, db_links)

    # 创建并启动线程
    for k,db_links in db_link_maps.items():
        thread = threading.Thread(target=worker, args=(db_links,checks_to_run,))
        threads.append(thread)
        thread.start()

    # 等待所有线程完成
    for thread in threads:
        thread.join()

    # 生成汇总报告
    generate_summary_html_report(all_results, os.path.join(new_output_report_dir, 'summary_report.html'))

    # 记录结束时间
    end_time = datetime.now()
    execution_time = end_time - start_time
    print(f"脚本执行结束,结束时间: [{end_time}],总耗时: [{execution_time}]")


#数据库连接信息

#db_links = []

db_link_maps ={}

#role_mode  # 运行模式 Primary_Sharding:分片节点 Primary_ReplicaSet:主从，三个节点 Primary_Single:归档节点 Master_Sharding:mongos节点
# 初始化检查组
check_groups = {
    "database_performance":  CheckGroup("数据库性能", "与数据库性能和配置相关的检查。",[
        CheckItem("MongoDB 版本检查", "", "output_contains","MONGODB_VERSION_CHECK","检查 MongoDB 服务器的版本。", RM_PRIMARY_REPLICASET),
        CheckItem("前 5 大数据库大小检查", "", "output_contains","TOP_5_DATABASES_SIZE_CHECK","检查前 5 大数据库的大小。", RM_MASTER_SHARDING),
        CheckItem("集合统计信息检查",  "", "output_contains","COLLECTION_STATS_CHECK","检查每个集合的存储、数据和索引大小。", RM_MASTER_SHARDING),
        CheckItem("服务器运行时间检查", "", "output_contains","SERVER_UPTIME_CHECK","检查 MongoDB 服务器的运行时间。", None),
        CheckItem("内存使用情况检查",  "", "output_contains","MEMORY_USAGE_CHECK","检查 MongoDB 服务器的内存使用情况。", None),
        CheckItem("操作计数器检查",  "", "output_contains","OPCOUNTERS_CHECK","检查执行的操作数量（插入、查询、更新、删除、命令）。", RM_PRIMARY_SINGLE),
        CheckItem("连接数检查", "", "output_contains","CONNECTIONS_CHECK","检查当前连接到 MongoDB 服务器的连接数。", RM_MASTER_SHARDING)
    ]),
    "database_performance2": CheckGroup("数据库性能2", "与数据库性能和配置相关的检查。", [
        CheckItem("操作计数器检查", "", "output_contains","OPCOUNTERS_CHECK","检查执行的操作数量（插入、查询、更新、删除、命令）。", RM_PRIMARY_SINGLE),
        CheckItem("连接数检查",  "", "output_contains","CONNECTIONS_CHECK","检查当前连接到 MongoDB 服务器的连接数。", RM_MASTER_SHARDING)
    ])
}

# 添加配置
CONFIG = {
    # 设置线程最大并发数
    'max_threads': 4,
    'outputReportDir': './reports/',
    'dblink_source':"mysql://root:my-secret-pw@127.0.0.1:3306/db_test" # 数据库链接源
}

if __name__ == '__main__':
    main()
