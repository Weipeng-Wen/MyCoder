"""内容搜索工具，使用正则表达式搜索文件内容。"""

import re  # 正则表达式
from pathlib import Path  # 文件路径
from .base import Tool  # 父类工具

# 跳过的目录列表
_SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", ".tox", "dist", "build"}


class GrepTool(Tool):
    name = "grep"
    description = (
        "Search file contents with regex. "
        "Returns matching lines with file path and line number."
    )
    parameters = {
        "type": "object",
        "properties": {
            "pattern": {  # 正则表达式模式
                "type": "string",
                "description": "Regex pattern to search for",
            },
            "path": {  # 搜索路径
                "type": "string",
                "description": "File or directory to search (default: cwd)",
            },
            "include": {  # 仅搜索匹配此glob的文件（例如'*.py'）
                "type": "string",
                "description": "Only search files matching this glob (e.g. '*.py')",
            },
        },
        "required": ["pattern"],
    }

    def execute(self, pattern: str, path: str = ".", include: str | None = None) -> str:

        # 正则表达式编译
        try:
            regex = re.compile(pattern)
        except re.error as e:
            return f"Invalid regex: {e}"

        # 获取搜索路径并判断是否存在
        base = Path(path).expanduser().resolve()
        if not base.exists():
            return f"Error: {path} not found"

        # 获取文件列表，如果是文件则直接搜索，如果是目录则递归搜索
        if base.is_file():
            files = [base]
        else:
            files = self._walk(base, include)

        # 搜索文件内容并返回匹配结果
        matches = []
        for fp in files:
            # 读取文件内容，忽略编码错误
            try:
                text = fp.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
                
            # 遍历每一行，查找匹配的行，并记录文件路径和行号
            for lineno, line in enumerate(text.splitlines(), 1):
                if regex.search(line):
                    matches.append(f"{fp}:{lineno}: {line.rstrip()}")
                    if len(matches) >= 200:
                        matches.append("... (200 match limit reached)")
                        return "\n".join(matches)

        return "\n".join(matches) if matches else "No matches found."

    # 静态方法，用于递归遍历目录树，跳过指定的目录，并返回匹配的文件列表
    @staticmethod
    def _walk(root: Path, include: str | None) -> list[Path]:
        """遍历目录树，跳过指定的目录，并返回匹配的文件列表。"""
        results = []
        # 遍历目录树，使用rglob方法匹配文件路径，如果指定了include参数，则只匹配符合glob模式的文件
        for item in root.rglob(include or "*"):
            
            # 跳过指定的目录
            if any(part in _SKIP_DIRS for part in item.relative_to(root).parts):
                continue

            # 如果是文件，则添加到结果列表中，如果结果列表长度超过5000，则停止遍历
            if item.is_file():
                results.append(item)
            if len(results) >= 5000:
                break
        return results
