"""File reading with line numbers."""

from pathlib import Path  # 面向对象的文件路径操作
from .base import Tool  # 工具父类


class ReadFileTool(Tool):
    name = "read_file"
    description = (
        "Read a file's contents with line numbers. "
        "Always read a file before editing it."
    )
    parameters = {
        "type": "object",
        "properties": {
            "file_path": {  # 文件路径
                "type": "string",
                "description": "Path to the file",
            },
            "offset": {  # 起始行号
                "type": "integer",
                "description": "Start line (1-based). Default 1.",
            },
            "limit": {  # 最大行数
                "type": "integer",
                "description": "Max lines to read. Default 2000.",
            },
        },
        "required": ["file_path"],
    }

    def execute(self, file_path: str, offset: int = 1, limit: int = 2000) -> str:
        try:
            # 检查文件路径是否存在且是文件
            p = Path(file_path).expanduser().resolve()
            if not p.exists():
                return f"Error: {file_path} not found"
            if not p.is_file():
                return f"Error: {file_path} is a directory, not a file"

            # 读取文件内容并按行分割
            text = p.read_text(encoding="utf-8", errors="replace")
            lines = text.splitlines()
            total = len(lines)

            # 计算起始行号和读取的行数
            start = max(0, offset - 1)
            chunk = lines[start : start + limit]
            numbered = [f"{start + i + 1}\t{ln}" for i, ln in enumerate(chunk)]
            result = "\n".join(numbered)

            # 如果总行数超过显示的范围，添加提示信息
            if total > start + limit:
                result += f"\n... ({total} lines total, showing {start+1}-{start+len(chunk)})"
            return result or "(empty file)"
        except Exception as e:
            return f"Error: {e}"
