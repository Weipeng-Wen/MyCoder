import time
from .base import Tool


class NowTimeTool(Tool):
    """获取当前日期和时间的工具"""
    
    name = "now_time"
    description = "Get the current time in a human-readable format."
    parameters = {
        "type": "object",
        "properties": {},
        "required": [],
    }

    def execute(self) -> str:
        return time.strftime("%Y-%m-%d %H:%M:%S")