from typing import Dict

from db_inspector.checks.base import CheckConfig, CheckGroup

# 检查配置的全局变量
CHECK_CONFIG = CheckConfig(check_groups=dict())
# 为了能在其他地方获取和修改配置，可以使用getter和setter
def get_check_config() -> CheckConfig:
    return CHECK_CONFIG

def set_check_config(new_config: CheckConfig):
    global CHECK_CONFIG
    CHECK_CONFIG = new_config

# class GlobalCheckConfig:
#     def __init__(self, config: CheckConfig):
#         self._config = config
#
#     @property
#     def config(self) -> CheckConfig:
#         """返回当前的检查配置"""
#         return self._config
#
#     @config.setter
#     def config(self, value: CheckConfig):
#         """设置新的检查配置"""
#         self._config = value
#
# # 初始化全局检查配置
# CHECK_CONFIG =None
# def set_config(config: CheckConfig):
#     global CHECK_CONFIG
#     CHECK_CONFIG= GlobalCheckConfig(config)


