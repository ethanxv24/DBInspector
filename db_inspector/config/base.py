from dataclasses import dataclass, field
from typing import List

# 检查项结构体
@dataclass
class Check:
    # 检查项所属的组名
    group: str = field(metadata={"remark": "检查项的组名"})
    # 检查项的列表
    checks: List[str] = field(default_factory=list,metadata={"remark": "检查项的名称列表"})

# 通用配置结构体
@dataclass
class GeneralConfig:
    # 日志级别
    log_level: str = field(metadata={"remark": "日志级别"})
    # 日志文件路径
    log_file: str = field(metadata={"remark": "日志文件路径"})
    # 日志格式（如 text、json 等）
    log_format: str = field(metadata={"remark": "日志格式"})
    # 默认报告格式（如 html、pdf 等）
    default_report_format: str = field(metadata={"remark": "默认报告格式"})
    # 默认报告保存目录
    default_report_dir: str = field(metadata={"remark": "默认报告保存目录"})
    # 配置的检查项组
    checks: List[Check] = field(default_factory=list,metadata={"remark": "配置的检查项组"})

# 数据库配置结构体
@dataclass
class Database:
    # 数据库类型（如 postgres）
    type: str = field(metadata={"remark": "数据库类型"})
    # 数据库名称
    name: str = field(metadata={"remark": "数据库名称"})
    # 数据库连接 URI
    uri: str = field(metadata={"remark": "数据库连接 URI"})
    # 数据库的检查项组
    checks: List[Check] = field(default_factory=list,metadata={"remark": "数据库的检查项组"})

# 配置文件的结构体
@dataclass
class Config:
    # 通用配置
    general: GeneralConfig = field(metadata={"remark": "通用配置"})
    # 数据库配置
    databases: List[Database] = field(metadata={"remark": "数据库配置"})
