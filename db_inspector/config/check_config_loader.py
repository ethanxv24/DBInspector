import os
import json

from db_inspector.checks.base import CheckItem, CheckGroup
from db_inspector.checks.constant import CheckConfig

def load_config_from_json(file_path: str) -> CheckConfig:
    """
    加载并解析 JSON 配置文件，并进行有效性检查。
    :param file_path: 配置文件路径
    :return: Config 对象，如果文件无效则返回 None
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
        with open(file_path, 'r') as f:
            data = json.load(f)
        print(f"Configuration file '{file_path}' loaded successfully.")

        # 动态解析 check_groups
        check_groups = {}
        for group_name, group_data in data.items():
            checks = {}
            for check_code,check_data in group_data['checks'].items() :
                check = CheckItem(
                    name=check_data["name"],
                    type=check_data["type"],
                    code = check_code,
                    remark=check_data["remark"],
                    query=check_data.get("query", ""),
                    command=check_data.get("command", ""),
                    expected_value=check_data.get("expected_value", ""),
                    check_type=check_data.get("check_type", ""),
                    comparison=check_data.get("comparison", "")
                )
                checks[check_code] = check
            group = CheckGroup(
                code=group_name,
                name=group_data["name"],
                remark=group_data["remark"],
                checks=checks
            )

            check_groups[group_name] = group
        config_obj = CheckConfig(check_groups=check_groups)

        return config_obj
    except json.JSONDecodeError as e:
        print(f"Error: The file '{file_path}' is not a valid JSON file. {str(e)}")
        return None
    except Exception as e:
        print(f"Error: An unexpected error occurred while loading the file '{file_path}'. {str(e)}")
        return None
