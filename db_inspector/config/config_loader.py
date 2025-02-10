import os
import toml
import yaml

from db_inspector.config.base import Config, GeneralConfig, Database, Check


def load_config_from_file_toml(file_path):
    """
    加载并解析 TOML 配置文件，并进行有效性检查。
    :param file_path: 配置文件路径
    :return: 配置内容（字典），如果文件无效则返回 None
    """
    # 检查文件是否存在
    if not os.path.exists(file_path):
        print(f"Error: The file '{file_path}' does not exist.")
        return None

    # 检查文件是否可读
    if not os.access(file_path, os.R_OK):
        print(f"Error: The file '{file_path}' is not readable.")
        return None

    # 检查文件是否为空
    if os.path.getsize(file_path) == 0:
        print(f"Error: The file '{file_path}' is empty.")
        return None

    # 尝试解析 TOML 格式
    try:
        config = toml.load(file_path)
        print(f"Configuration file '{file_path}' loaded successfully.")
        return config
    except toml.TomlDecodeError as e:
        print(f"Error: The file '{file_path}' is not a valid TOML file. {str(e)}")
        return None
    except Exception as e:
        print(f"Error: An unexpected error occurred while loading the file '{file_path}'. {str(e)}")
        return None

def load_config_from_yml(file_path: str) -> Config:
    """
    加载并解析 YAML 配置文件，并将其转换为 Config 对象。
    :param file_path: 配置文件路径
    :return: Config 对象
    """
    # 检查文件是否存在
    if not os.path.exists(file_path):
        print(f"Error: The file '{file_path}' does not exist.")
        return None

    # 检查文件是否可读
    if not os.access(file_path, os.R_OK):
        print(f"Error: The file '{file_path}' is not readable.")
        return None

    # 检查文件是否为空
    if os.path.getsize(file_path) == 0:
        print(f"Error: The file '{file_path}' is empty.")
        return None

    # 尝试解析 JSON 格式
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        print(f"Configuration file '{file_path}' loaded successfully.")

        # 解析 general 配置部分
        general_data = data.get("general", {})
        general_config = GeneralConfig(
            log_level=general_data.get("log_level", "info"),  # 默认值为 "info"
            log_file=general_data.get("log_file", "db_inspector.log"),  # 默认文件名
            log_format=general_data.get("log_format", "text"),  # 默认格式
            default_report_format=general_data.get("default_report_format", "html"),  # 默认报告格式
            default_report_dir=general_data.get("default_report_dir", "reports"),  # 默认报告目录
            checks=[
                Check(**check) for check in general_data.get("checks", [])  # 如果没有 checks，则使用空列表
            ]
        )

        # 解析 databases 配置部分
        databases_data = data.get("databases", [])
        databases = [
            Database(
                type=db.get("type", "postgres"),  # 默认数据库类型为 postgres
                name=db.get("name", ""),
                uri=db.get("uri", ""),
                checks=[Check(**check) for check in db.get("checks", [])]  # 如果没有 checks，则使用空列表
            )
            for db in databases_data
        ]

        return Config(general=general_config, databases=databases)
    except yaml.YAMLError as e:
        print(f"Error: The file '{file_path}' is not a valid YAML file. {str(e)}")
        return None
    except Exception as e:
        print(f"Error: An unexpected error occurred while loading the file '{file_path}'. {str(e)}")
        return None
