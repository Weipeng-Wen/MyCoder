"""文件写入工具类"""

from pathlib import Path  # 面向对象的文件路径操作
from .base import Tool  # 父类方法
from .edit import _changed_files  # 记录已经更改的文件路径


class WriteFileTool(Tool):
    name = "write_file"
    description = (
        "Create a new file or completely overwrite an existing one. "
        "For small edits to existing files, prefer edit_file instead."
    )
    parameters = {
        "type": "object",
        "properties": {
            "file_path": {  # 文件路径
                "type": "string",
                "description": "Path for the file",
            },
            "content": {  # 文件内容
                "type": "string",
                "description": "Full file content to write",
            },
        },
        "required": ["file_path", "content"],
    }

    def execute(self, file_path: str, content: str) -> str:
        try:
            # 解析文件路径并创建父目录
            p = Path(file_path).expanduser().resolve()
            p.parent.mkdir(parents=True, exist_ok=True)

            # 写入文件内容并记录更改
            p.write_text(content, encoding="utf-8")
            _changed_files.add(str(p))
            n_lines = content.count("\n") + (1 if content and not content.endswith("\n") else 0)
            return f"Wrote {n_lines} lines to {file_path}"
        except Exception as e:
            return f"Error: {e}"
