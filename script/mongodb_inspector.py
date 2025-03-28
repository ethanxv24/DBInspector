import yaml
import json
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from jinja2 import Template
import os
import argparse  # 导入argparse库

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




# 定义检查项类
class CheckItem:
    # 定义检查项名称到方法名的映射
    METHOD_MAP = {
        "MONGODB_VERSION_CHECK": "mongodb_version_check",
        "TOP_5_DATABASES_SIZE_CHECK": "top_5_databases_size_check",
        "COLLECTION_STATS_CHECK": "collection_stats_check",
        "SERVER_UPTIME_CHECK": "server_uptime_check",
        "MEMORY_USAGE_CHECK": "memory_usage_check",
        "OPCOUNTERS_CHECK": "opcounters_check",
        "CONNECTIONS_CHECK": "connections_check"
    }

    def __init__(self, name,expected_value, check_type,exec_func,remark):
        self.name = name
        #self.query = query
        self.remark = remark
        self.exec_func = self.METHOD_MAP.get(exec_func)
        self.expected_value = expected_value
        self.check_type = check_type

    def execute(self, client):
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
                'status': status,
                'actual_result': actual_result,
                'expected_result': self.expected_value
            }
        except Exception as e:
            return {
                'status': 'Error',
                'actual_result': str(e),
                'expected_result': self.expected_value
            }

    '''
        获取MongoDB版本信息
        db.version()
    '''
    def mongodb_version_check(self, client):
        return client.admin.command('serverStatus')['version']

    '''
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
    '''
    def top_5_databases_size_check(self, client):
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

    '''
    节点角色状态：
    var a = rs.status(); 
    a.members.forEach(function(e){print(e.name, e.stateStr)})
    '''
    def collection_stats_check(self, client):
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

    def server_uptime_check(self, client):
        return client.admin.command('serverStatus')['uptime']

    def memory_usage_check(self, client):
        return client.admin.command('serverStatus')['mem']

    def opcounters_check(self, client):
        return client.admin.command('serverStatus')['opcounters']

    def connections_check(self, client):
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
            result = check.execute(client)
            results[f"{db_name} - {check.name}"] = result
        return results



# 加载配置文件
def load_config(config_path):
    with open(config_path, 'r', encoding='utf-8') as file:
        config = yaml.safe_load(file)
    return config


# 执行检查
def perform_checks(db_name, client, check_groups, checks_to_run):
    results = {}
    for check_group_name, check_group in check_groups.items():
        if check_group_name in checks_to_run:
            results.update(check_group.perform_checks(db_name, client))
    return results

# 生成HTML报告
def generate_html_report(results, output_path, db_name=None):
    template = Template('''
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
            tr:nth-child(even) {
                background-color: #f9f9f9;
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
        </style>
    </head>
    <body>
        <div class="{{ 'summary-report' if not db_name else 'database-report' }}">
            <h1>{{ 'MongoDB Inspection Summary Report' if not db_name else 'MongoDB Inspection Report' }}</h1>
            {% if db_name %}
            <h2>Database: {{ db_name }}</h2>
            {% else %}
            <div class="links">
                {% for db, _ in results.items() %}
                <a href="{{ db.replace(' ', '_') }}_report.html">{{ db }}</a>
                {% endfor %}
            </div>
            {% endif %}
            <table border="1">
                <tr>
                    <th>Check Item</th>
                    <th>Status</th>
                    <th>Actual Result</th>
                    <th>Expected Result</th>
                </tr>
                {% for name, result in results.items() %}
                <tr>
                    <td>{{ name }}</td>
                    <td>{{ result.status }}</td>
                    <td>{{ result.actual_result }}</td>
                    <td>{{ result.expected_result }}</td>
                </tr>
                {% endfor %}
            </table>
        </div>
    </body>
    </html>
    ''')
    html_content = template.render(results=results, db_name=db_name)
    with open(output_path, 'w', encoding='utf-8') as file:
        file.write(html_content)

# 主函数
def main():
    # 定义命令行参数
    parser = argparse.ArgumentParser(description='MongoDB Inspector Script')
    parser.add_argument('--config', type=str, default='./config.yml', help='Path to the configuration file')
    parser.add_argument('--output-report-dir', type=str, default='./reports/', help='Path to the output HTML report')
    args = parser.parse_args()

    config_path = args.config
    output_report_dir = args.output_report_dir

    # 检查并创建输出目录
    if not os.path.exists(output_report_dir):
        os.makedirs(output_report_dir)

    # 加载配置文件
    config = load_config(config_path)
    all_results = {}

    # 配置有效，继续进行后续操作
    for db_config in config['databases']:

        uri = db_config['uri']
        db_name = db_config['name']
        client = MongoClient(uri, server_api=ServerApi('1'))
        db_checks = db_config.get('checks', [])

        # 如果没有自定义检查组，则使用所有检查项
        if not db_checks:
            checks_to_run = check_groups.keys()
        else:
            checks_to_run = [check_group['group'] for check_group in db_checks]

        db_results = {}

        # 遍历每个检查组
        for check_group in checks_to_run:
            if check_group in check_groups:
                group_checks = check_groups[check_group]
                results = group_checks.perform_checks(db_name, client)
                db_results.update(results)

        client.close()

        # 生成每个数据库的详细报告
        generate_html_report(db_results, os.path.join(output_report_dir, f'{db_name}_report.html'), db_name)

        # 汇总结果
        all_results.update(db_results)

    # 生成汇总报告
    generate_html_report(all_results, os.path.join(output_report_dir, 'summary_report.html'))


# 初始化检查组
check_groups = {
    "database_performance":  CheckGroup("数据库性能", "与数据库性能和配置相关的检查。",[
        CheckItem("MongoDB 版本检查", "", "output_contains","MONGODB_VERSION_CHECK","检查 MongoDB 服务器的版本。"),
        CheckItem("前 5 大数据库大小检查", "", "output_contains","TOP_5_DATABASES_SIZE_CHECK","检查前 5 大数据库的大小。"),
        CheckItem("集合统计信息检查",  "", "output_contains","COLLECTION_STATS_CHECK","检查每个集合的存储、数据和索引大小。"),
        CheckItem("服务器运行时间检查", "", "output_contains","SERVER_UPTIME_CHECK","检查 MongoDB 服务器的运行时间。"),
        CheckItem("内存使用情况检查",  "", "output_contains","MEMORY_USAGE_CHECK","检查 MongoDB 服务器的内存使用情况。"),
        CheckItem("操作计数器检查",  "", "output_contains","OPCOUNTERS_CHECK","检查执行的操作数量（插入、查询、更新、删除、命令）。"),
        CheckItem("连接数检查", "", "output_contains","CONNECTIONS_CHECK","检查当前连接到 MongoDB 服务器的连接数。")
    ]),
    "database_performance2": CheckGroup("数据库性能2", "与数据库性能和配置相关的检查。", [
        CheckItem("操作计数器检查", "", "output_contains","OPCOUNTERS_CHECK","检查执行的操作数量（插入、查询、更新、删除、命令）。"),
        CheckItem("连接数检查",  "", "output_contains","CONNECTIONS_CHECK","检查当前连接到 MongoDB 服务器的连接数。")
    ])
}


if __name__ == '__main__':
    main()
