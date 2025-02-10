from abc import abstractmethod
from enum import Enum
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Dict


class Status(Enum):
    SUCCESS = 'success'
    FAILURE = 'failure'
    WARNING = 'warning'

class CheckItemResult:
    def __init__(self, check_name, status,message):
        self.check_name = check_name
        self.status = status
        self.message = message

class BaseCheck:
    @abstractmethod
    def run(self, db_connection):
        raise NotImplementedError("This method should be overridden by subclasses")


@dataclass
class CheckItem:
    # 检查项的名称
    name: str = field(metadata={"remark": "检查项的名称"})
    # 检查项类型，例如 'sql' 或 'shell'
    type: str = field(metadata={"remark": "检查项类型（sql/shell）"})
    # 检查项的唯一标识符
    code: str = field(metadata={"remark": "检查项的唯一标识符"})
    # 对检查项的描述和备注信息
    remark: str = field(metadata={"remark": "对检查项的描述"})
    # 针对 SQL 类型检查的 SQL 查询语句（非 SQL 类型时可为空）
    query: str = field(default="", metadata={"remark": "SQL 查询语句，仅在 type 为 sql 时使用"})
    # 针对 Shell 类型检查的命令（非 shell 类型时可为空）
    command: str = field(default="", metadata={"remark": "Shell 命令，仅在 type 为 shell 时使用"})
    # 预期的检查值，依据 check_type 进行判断
    expected_value: str = field(default="", metadata={"remark": "预期的检查值"})
    # 检查类型，例如 'threshold'（阈值比较）或 'output_contains'（输出包含检查）
    check_type: str = field(default="", metadata={"remark": "检查类型，用于指定判断方式"})
    # 如果是阈值检查，比较操作符，例如 'greater_than', 'less_than', 'equal_to'
    comparison: str = field(default="", metadata={"remark": "比较操作符，仅在阈值检查时使用"})

@dataclass
class CheckGroup:
    # 分组的唯一标识符
    code: str = field(metadata={"remark": "分组的唯一标识符"})
    # 分组名称
    name: str = field(metadata={"remark": "分组的名称"})
    # 分组的描述和备注信息
    remark: str = field(metadata={"remark": "对分组的描述"})
    # 分组下包含的所有检查项 检查项字典，以 code 为键
    checks: Dict[str, CheckItem] = field(metadata={"remark": "检查项字典，键为检查项 code，值为 Check 对象"})

@dataclass
class CheckConfig:
    # 动态的检查项组（字典形式，键是组名，值是对应的 CheckGroup）
    check_groups: Dict[str, CheckGroup] = field(metadata={"remark": "动态的检查项组，键为组名，值为 CheckGroup 对象"})


@contextmanager
def manage_transaction(connection):
    cursor = connection.cursor()
    try:
        yield cursor
        connection.commit()  # 正常结束时提交事务
    except Exception as exc:
        connection.rollback()  # 出错时回滚事务
        raise exc
    finally:
        cursor.close()
