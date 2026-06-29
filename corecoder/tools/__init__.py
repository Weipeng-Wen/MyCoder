"""Tool registry."""

from .bash import BashTool
from .read import ReadFileTool
from .write import WriteFileTool
from .edit import EditFileTool
from .glob_tool import GlobTool
from .grep import GrepTool
from .agent import AgentTool
from .now_time import NowTimeTool


# 列举所有工具
ALL_TOOLS = [
    BashTool(),  # 执行 Bash 命令
    ReadFileTool(),  # 读取文件
    WriteFileTool(),  # 写入文件
    EditFileTool(),  # 编辑文件
    GlobTool(),  # 匹配文件路径
    GrepTool(),  # 搜索文本
    AgentTool(),  # 代理工具
    NowTimeTool(),  # 获取当前时间
]


def get_tool(name: str):
    """Look up a tool by name."""
    for t in ALL_TOOLS:
        if t.name == name:
            return t
    return None
