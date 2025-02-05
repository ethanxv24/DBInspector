import os
import toml

def load_config_from_file(file_path):
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
