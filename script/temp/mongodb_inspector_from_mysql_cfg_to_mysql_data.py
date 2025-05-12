import os
import threading
from datetime import datetime
import mysql.connector
from mysql.connector import Error
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

''' readme
    MongoDB Inspection Report
    
    1. 使用方法 python3 环境 安装特定依赖
        pip3 install pymongo==4.11.3 mysql-connector-python==8.0.26
    2. 设置数据库执行配置
        [CONFIG]配置
        [DBLINKS_SQL] 查询sql修正
    3. 执行
        python3 ./mongodb_inspector.py
'''

DB_TYPE_MONGODB = 'mongo' # 数据库类型 固定

# Role mode 常量
RM_PRIMARY_REPLICASET = "Primary_ReplicaSet"
RM_MASTER_SHARDING = "Master_Sharding"
RM_PRIMARY_SHARDING = "Primary_Sharding"
RM_PRIMARY_SINGLE = "Primary_Single"

# 相关SQL
DBLINKS_SQL = '''select * from my_table;''' # 数据源sql
GET_MAX_BATCHID_SQL = '''SELECT COALESCE(MAX(t.batchid), 0) AS max_batchid FROM inspec_db_info t WHERE t.dt = %s;''' # 获取最大batchid
BATCH_INSERT_INSPEC_SQL = '''INSERT INTO inspec_db_info (dbtype, clustername, instance, metric_name, metric_value, datetime, batchid, dt) VALUES (%s,%s, %s, %s, %s, %s, %s, %s)''' # 数据库信息批量插入

# 定义自定义异常类
class CustomError(Exception):
    def __init__(self, message="这是一个自定义错误"):
        self.message = message
        super().__init__(self.message)

# 定义检查项类
class CheckItem:
    # 定义检查项名称到方法名的映射
    METHOD_MAP = {
        "MONGODB_VERSION_CHECK": "check_mongodb_version", # 检查MongoDB版本
        "TOP_5_DATABASES_SIZE_CHECK": "check_top_5_databases_size", # 检查数据库大小
        "COLLECTION_STATS_CHECK": "check_collection_stats", # 检查集合统计信息
        "SERVER_UPTIME_CHECK": "check_server_uptime", # 检查服务器运行时间
        "MEMORY_USAGE_CHECK": "check_memory_usage", # 检查内存使用情况
        "OPCOUNTERS_CHECK": "check_opcounters", # 检查opcounters
        "CONNECTIONS_CHECK": "check_connections", # 检查连接数
        "CLUSTER_STATUS_CHECK":"check_cluster_status", # 检查集群状态
        "SHARDS_STATUS_CHECK": "check_shards_status",  # 获取分片信息
        "DATABASES_STATUS_CHECK": "check_databases_status"  # 获取数据库分片信息
    }

    def __init__(self, name, exec_func, remark, role_mode=None):
        self.name = name
        self.remark = remark
        self.exec_func = self.METHOD_MAP.get(exec_func)
        self.role_mode = role_mode  # 运行模式 Primary_Sharding:分片节点 Primary_ReplicaSet:主从，三个节点 Primary_Single:归档节点 Master_Sharding:mongos节点

    def execute(self, client, db_link):
        try:
            method = getattr(self, self.exec_func)
            actual_result = method(client)

            results = []
            # 循环 actual_result map
            for k, v in actual_result.items():
                results.append((DB_TYPE_MONGODB,db_link['instance_name'], db_link['node_group_name'],k,v, datetime.now(),  BATCH_ID, CURRENT_DT))


            # actual_result 转成string
            #actual_result = str(actual_result)

            return results

        except Exception as e:
            print(f"--------发生错误: {e} [execute] ")

        return []

    def check_mongodb_version(self, client):
        # 获取MongoDB版本信息 db.version()
        try:
            # 检查 MongoDB 服务器的版本
            # 执行 serverStatus 命令并获取版本信息
            server_status = client.admin.command('serverStatus')
            return {'mongodb_version_check':server_status['version']}
        except Exception as e:
            print(f"--------发生错误: {e} [check_mongodb_version] ")

    def check_top_5_databases_size(self, client):
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
            '存储大小': f"{total_storage_size / 1024 / 1024:.2f} MB",
            '数据大小': f"{total_data_size / 1024 / 1024:.2f} MB",
            '索引大小': f"{total_index_size / 1024 / 1024:.2f} MB"
        })

        # 按照数据大小排序并取前5
        sorted_databases = sorted(database_sizes, key=lambda x: float(x['数据大小'].split()[0]), reverse=True)

        # 构建字符串输出
        result_str = "Top 5 Databases by Data Size:\n"
        for item in sorted_databases[:5]:
            result_str += (
                f"Database: {item['name']}\n"
                f"  Storage Size: {item['存储大小']}\n"
                f"  Data Size: {item['数据大小']}\n"
                f"  Index Size: {item['索引大小']}\n"
            )

        return {'check_top_5_databases_size':result_str}

    def check_collection_stats(self, client):
        # 检查每个集合的存储、数据和索引大小
        # 执行 rs.status() 命令
        '''
        节点角色状态：
        var a = rs.status();
        a.members.forEach(function(e){print(e.name, e.stateStr)})
        '''
        rs_status = client.admin.command('replSetGetStatus')

        # 遍历成员列表
        db_stats = []
        for member in rs_status.get('members', []):
            name = member.get('name')
            state_str = member.get('stateStr')
            print(name, state_str)
            db_stats.append({ 'name': member.get('name'), 'stats':  member.get('stateStr') })
        return {'check_collection_stats':db_stats}

    def check_server_uptime(self, client):
        # 检查 MongoDB 服务器的运行时间 db.serverStatus().uptime
        return {'servie_up_time':client.admin.command('serverStatus')['uptime']}

    def check_memory_usage(self, client):
        # 检查 MongoDB 服务器的内存使用情况 db.serverStatus().mem
        mem_data =  client.admin.command('serverStatus')['mem']
        return {
            'memory_use_check_bits': mem_data['bits'],
            'memory_use_check_resident': mem_data['resident'],
            'memory_use_check_virtual': mem_data['virtual'],
        }

    def check_opcounters(self, client):
        # 检查执行的操作数量（插入、查询、更新、删除、命令） db.serverStatus().opcounters
        return client.admin.command('serverStatus')['opcounters']

    def check_connections(self, client):
        # 检查当前连接到 MongoDB 服务器的连接数 db.serverStatus().connections
        connections_data = client.admin.command('serverStatus')['connections']

        return {
            'check_connections_current': connections_data['current'],
            'check_connections_available': connections_data['available'],
            'check_connections_active': connections_data['active']
        }

    def check_cluster_status(self, client):
        # 节点角色状态：
        # var a = rs.status();
        # a.members.forEach(function(e){print(e.name, e.stateStr)})

        cluster_status = client.admin.command('replSetGetStatus')
        result = []
        # 添加集群名称
        result.append(f'RS Name: {cluster_status.get("set")}')
        result.append('Members:')

        # 处理每个成员的信息
        for member in cluster_status.get('members', []):
            result.append(f"- ID: {member.get('_id')} Host: {member.get('name')} State: {member.get('stateStr')} Is Primary: {member.get('stateStr') == 'PRIMARY'} Is Secondary: {member.get('stateStr') == 'SECONDARY'}")
            # result.append(f"Host: {member.get('name')}")
            # result.append(f"State: {member.get('stateStr')}")
            # result.append(f"Is Primary: {member.get('stateStr') == 'PRIMARY'}")
            # result.append(f"Is Secondary: {member.get('stateStr') == 'SECONDARY'}")
            # result.append("----------------------")

        # 使用 '\n' 连接所有元素
        return {'member_role_status':'\n'.join(result)}

    def is_mongos(self,client):
        try:
            result = client.admin.command("ismaster")
            return result.get("msg") == "isdbgrid"
        except:
            return False

    def check_shards_status(self, client):
        if not self.is_mongos(client):
            raise CustomError('当前连接不是 mongos 实例，无法执行 sh.status()。')

        try:
            sh_status = client.admin.command("shStatus")
            return {'check_shards_status': sh_status.get("shards", {})}
        except Exception as e:
            print(f"--------发生错误: {e} [check_shards_status] ")
            return str(e)

    def check_databases_status(self, client):
        if not self.is_mongos(client):
            raise CustomError('当前连接不是 mongos 实例，无法执行 sh.status()。')

        try:
            sh_status = client.admin.command('shStatus')
            databases_info = sh_status.get('databases', {})

            formatted_output = []
            for db_id, db_info in databases_info.items():
                formatted_output.append(
                    f"db: {db_id}\n"
                    f"primary: {db_info.get('primary')}\n"
                    f"partitioned: {db_info.get('partitioned')}\n"
                )

            return {'check_databases_status': '\n'.join(formatted_output)}
        except Exception as e:
            print(f"--------发生错误: {e} [check_databases_status] ")
            return str(e)

# 执行检查
def perform_checks(db_link, client):
    results = []
    for check in CHECK_ITEMS:
        if (check.role_mode is None) or \
                (check.role_mode ==db_link['role_mode']):
            check_item_start_time = datetime.now()
            result = check.execute(client, db_link)

            # 记录日志
            check_item_end_time = datetime.now()
            check_item_execution_time = check_item_end_time - check_item_start_time
            # 如果判断执行时长 分别对超过2s、5s、20s 的情况进行不同程度的日志输出
            if check_item_execution_time.total_seconds() > 20:
                print(f"--------[!!!]执行时间超过20s,耗时:[{check_item_execution_time}],detail:[{db_link['instance_name']}] | [{db_link['role_mode']}] | [{check.name}]")
            elif check_item_execution_time.total_seconds() > 5:
                print(f"--------[!!]执行时间超过5s,耗时:[{check_item_execution_time}],detail:[{db_link['instance_name']}] | [{db_link['role_mode']}] | [{check.name}]")
            elif check_item_execution_time.total_seconds() > 2:
                print(f"--------[!]执行时间超过2s,耗时:[{check_item_execution_time}],detail:[{db_link['instance_name']}] | [{db_link['role_mode']}] | [{check.name}]")

            results.extend(result)
    return results

# 获取MySQL连接配置
def get_mysql_connection_config():
    try:
        # 从配置中提取MySQL URL
        mysql_url = CONFIG.get('dblink_source', '')

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
        db_config = {'host': domain,'database': database,'user': user,'password': password}
        return db_config

    except (ValueError, KeyError, AttributeError) as e:
        print(f"--Configuration Error: {e}")
    except Exception as e:
        print(f"--Unexpected Error: {e}")
    return None  # 显式返回 None 避免结构歧义

#  获取数据库连接
def get_mysql_connection():
    return mysql.connector.connect(**get_mysql_connection_config())

# 获取数据库链接数据
def fetch_db_link_data():
    try:
        print(f"--正在从mysql库查询MongoDB巡检数据, 查询sql为: [{DBLINKS_SQL}]")

        # 获取数据库链接数据
        mysql_conn = get_mysql_connection()

        # 使用上下文管理器管理数据库连接和游标
        with mysql_conn as connection:
            if not connection.is_connected():
                raise ConnectionError("Failed to connect to the database")

            with connection.cursor(dictionary=True) as cursor:
                # 执行SQL查询
                cursor.execute(DBLINKS_SQL)
                rows = cursor.fetchall()
                for index, row in enumerate(rows):
                    DB_LINKS.append({'instance_name':row['instance_name'], 'environment':row['environment'], 'role_mode':row['role_mode'], 'node_group_name':row['node_group_name'],'data_path':row['data_path']})

    except Error as e:
        print(f"--MySQL Error: {e}")
    except Exception as e:
        print(f"--Unexpected Error: {e}")
    finally:
        print(f"--mysql数据库巡检数据查询完成,从mysql库查询到MongoDB巡检数据，共 [{len(rows)}] 条数据")

# 获取最大批次ID
def get_max_batch_id(dt: str):
    try:
        print(f"--正在从mysql库查询MongoDB巡检数据, 查询sql为: [{GET_MAX_BATCHID_SQL}]")

        # 获取数据库链接数据
        mysql_conn = get_mysql_connection()

        # 使用上下文管理器管理数据库连接和游标
        with mysql_conn as connection:
            if not connection.is_connected():
                raise ConnectionError("Failed to connect to the database")

            with connection.cursor(dictionary=True) as cursor:
                # 使用参数化查询传入 dt
                cursor.execute(GET_MAX_BATCHID_SQL, (dt,))
                result = cursor.fetchone()
                max_batchid = result['max_batchid'] if result else 0

                return max_batchid

    except Error as e:
        print(f"--MySQL Error: {e}")
    except Exception as e:
        print(f"--Unexpected Error: {e}")
    finally:
        print(f"--mysql最大批次ID查询完成，dt:[{dt}],max(batchid):[{max_batchid}]")
    return 0

#  批量插入数据
def batch_insert():
    print(f"--开始批量插入数据")
    connection = None
    cursor = None
    try:
        # 获取数据库链接数据
        connection = get_mysql_connection()

        if connection.is_connected():
            cursor = connection.cursor()

            # 设置每批处理的数量
            batch_size = CONFIG['batch_size']

            # 确保 BATCH_INSERT_DATA 是一个非空列表
            if not isinstance(BATCH_INSERT_DATA, list) or not BATCH_INSERT_DATA:
                print("--BATCH_INSERT_DATA 数据为空或格式错误")
                return False


            total = len(BATCH_INSERT_DATA)
            for i in range(0, total, batch_size):
                batch = BATCH_INSERT_DATA[i:i + batch_size]
                cursor.executemany(BATCH_INSERT_INSPEC_SQL, batch)
                connection.commit()
                if i > 0 and i % 1000 == 0:
                    print(f"已处理 {i}/{total} 条记录")

            return True

    except Error as e:
        if connection:
            connection.rollback()
        print(f"--Unexpected Error: {e}")
        return False
    except Exception as e:
        print(f"--Unexpected Error: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

#全局数据集
BATCH_INSERT_DATA = []
# 线程锁，用于线程安全
lock = threading.Lock()

# 主函数
def main():
    # 记录开始时间
    start_time = datetime.now()
    print(f"脚本开始执行时间: [{start_time}]")  # 新增输出开始时间

    # 获取数据库链接数据
    fetch_db_link_data()

    if not DB_LINKS:
        print("--No database links found. Exiting...")
        return

    # 获取最大批次ID
    global BATCH_ID
    BATCH_ID  = get_max_batch_id(CURRENT_DT)+1

    # 任务列表
    threads = []
    # 创建一个信号量对象，最大并发数为 4
    semaphore = threading.Semaphore(CONFIG['max_threads'])

    def worker(db_link):
        global BATCH_INSERT_DATA
        # 获取信号量，如果达到最大并发数，线程会阻塞
        with semaphore:

            if None == db_link:
                print("--No database links found. Exiting...")
                return

            results = []

            with MongoClient(db_link['data_path'], server_api=ServerApi('1')) as client:
                check_results = perform_checks(db_link, client)
                results.extend(check_results)

            with lock:
                # 汇总结果
                BATCH_INSERT_DATA.extend(results)

    # 创建并启动线程
    for db_link in DB_LINKS:
        thread = threading.Thread(target=worker, args=(db_link,))
        threads.append(thread)
        thread.start()

    # 等待所有线程完成
    for thread in threads:
        thread.join()

    # 批量执行
    batch_insert()

    # 记录结束时间
    end_time = datetime.now()
    execution_time = end_time - start_time
    print(f"脚本执行结束,结束时间: [{end_time}],总耗时: [{execution_time}]")


BATCH_ID = 0 # 批次ID
CURRENT_DT = datetime.now().strftime("%Y%m%d") # 当前日期

#数据库连接信息
DB_LINKS = []

#role_mode  # 运行模式 Primary_Sharding:分片节点 Primary_ReplicaSet:主从，三个节点 Primary_Single:归档节点 Master_Sharding:mongos节点
# 初始化检查项
CHECK_ITEMS = {
        CheckItem("db分片信息", "DATABASES_STATUS_CHECK", "获取 sh.status().databases 并格式化输出每个数据库的 _id、primary、partitioned 状态。", RM_MASTER_SHARDING),
        CheckItem("集群分片信息",  "SHARDS_STATUS_CHECK", "获取 sh.status().shards 的内容，显示所有分片的信息。", RM_MASTER_SHARDING),
        CheckItem("集群状态检查", "CLUSTER_STATUS_CHECK","检查 MongoDB 集群状态，并输出 rs.status().set 和 rs.status().members._id, name, health, stateStr 信息。", RM_PRIMARY_REPLICASET),
        CheckItem("MongoDB 版本检查", "MONGODB_VERSION_CHECK","检查 MongoDB 服务器的版本。", RM_PRIMARY_REPLICASET),
        CheckItem("前 5 大数据库大小检查", "TOP_5_DATABASES_SIZE_CHECK","检查前 5 大数据库的大小。", RM_MASTER_SHARDING),
        CheckItem("集合统计信息检查",  "COLLECTION_STATS_CHECK","检查每个集合的存储、数据和索引大小。", RM_MASTER_SHARDING),
        CheckItem("服务器运行时间检查", "SERVER_UPTIME_CHECK","检查 MongoDB 服务器的运行时间。", None),
        CheckItem("内存使用情况检查",  "MEMORY_USAGE_CHECK","检查 MongoDB 服务器的内存使用情况。", None),
        CheckItem("操作计数器检查",  "OPCOUNTERS_CHECK","检查执行的操作数量（插入、查询、更新、删除、命令）。", RM_PRIMARY_SINGLE),
        CheckItem("连接数检查", "CONNECTIONS_CHECK","检查当前连接到 MongoDB 服务器的连接数。", RM_MASTER_SHARDING),
}

# 添加配置
CONFIG = {
    'max_threads': 4,  # 设置线程最大并发数
    'batch_size' :1000, # 设置每批处理的数量
    'dblink_source':"mysql://root:my-secret-pw@127.0.0.1:3306/db_test" # 数据库链接源
}

if __name__ == '__main__':
    main()
