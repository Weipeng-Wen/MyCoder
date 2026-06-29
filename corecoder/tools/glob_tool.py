"""文件路径匹配工具"""

from pathlib import Path  # 文件路径
from .base import Tool  # 工具父类


class GlobTool(Tool):
    name = "glob"
    description = (
        "Find files matching a glob pattern. "
        "Supports ** for recursive matching (e.g. '**/*.py')."
    )
    parameters = {
        "type": "object",
        "properties": {
            "pattern": {  # 全局匹配模式
                "type": "string",
                "description": "Glob pattern, e.g. '**/*.py' or 'src/**/*.ts'",
            },
            "path": {  # 路径
                "type": "string",
                "description": "Directory to search in (default: cwd)",
            },
        },
        "required": ["pattern"],
    }

    def execute(self, pattern: str, path: str = ".") -> str:
        try:
            # 获取路径并判断是否为目录
            base = Path(path).expanduser().resolve()
            if not base.is_dir():
                return f"Error: {path} is not a directory"

            # 匹配文件路径，并按修改时间排序
            hits = list(base.glob(pattern))
            hits.sort(key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True)

            # 只显示前 100 个匹配结果
            total = len(hits)
            shown = hits[:100]
            lines = [str(h) for h in shown]
            result = "\n".join(lines)

            # 如果匹配结果超过 100 个，提示用户
            if total > 100:
                result += f"\n... ({total} matches, showing first 100)"
            return result or "No files matched."
        except Exception as e:
            return f"Error: {e}"
