"""编辑文件工具"""

import difflib  # 文本差异比较
from pathlib import Path  # 面向对象的文件路径操作

from .base import Tool  # 父类方法

# 记录已更改的文件路径
_changed_files: set[str] = set()


class EditFileTool(Tool):
    name = "edit_file"
    description = (
        "Edit a file by replacing an exact string match. "
        "old_string must appear exactly once in the file for safety. "
        "Include enough surrounding context to ensure uniqueness."
    )
    parameters = {
        "type": "object",
        "properties": {
            "file_path": {  # 文件路径
                "type": "string",
                "description": "Path to the file to edit",
            },
            "old_string": {  # 旧字符串
                "type": "string",
                "description": "Exact text to find (must be unique in file)",
            },
            "new_string": {  # 新字符串
                "type": "string",
                "description": "Replacement text",
            },
        },
        "required": ["file_path", "old_string", "new_string"],
    }

    def execute(self, file_path: str, old_string: str, new_string: str) -> str:
        try:
            # 解析文件路径，展开用户目录并获取绝对路径
            p = Path(file_path).expanduser().resolve()
            if not p.exists():
                return f"Error: {file_path} not found"

            # 读取文件内容，确保是 UTF-8 编码
            try:
                content = p.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                return f"Error: {file_path} is not a UTF-8 text file (edit_file only edits text files)"
            
            # 检查 old_string 在文件中出现的次数
            occurrences = content.count(old_string)

            # 如果 old_string 没有出现，或者出现多次，返回错误信息
            if occurrences == 0:
                preview = content[:500] + ("..." if len(content) > 500 else "")
                return (
                    f"Error: old_string not found in {file_path}.\n"
                    f"File starts with:\n{preview}"
                )
            if occurrences > 1:
                # 如果 old_string 出现多次，提示用户提供更多上下文以确保唯一性
                return (
                    f"Error: old_string appears {occurrences} times in {file_path}. "
                    f"Include more surrounding lines to make it unique."
                )

            # 替换 old_string 为 new_string，并写回文件
            new_content = content.replace(old_string, new_string, 1)
            p.write_text(new_content, encoding="utf-8")
            _changed_files.add(str(p))

            # 生成并返回统一差异格式的 diff，显示文件编辑前后的变化
            diff = _unified_diff(content, new_content, str(p))
            return f"Edited {file_path}\n{diff}"
        except Exception as e:
            return f"Error: {e}"


def _unified_diff(old: str, new: str, filename: str, context: int = 3) -> str:
    """生成统一差异格式的diff,显示文件编辑前后的变化"""
    old_lines = old.splitlines(keepends=True)
    new_lines = new.splitlines(keepends=True)
    diff = difflib.unified_diff(
        old_lines, new_lines,
        fromfile=f"a/{filename}", tofile=f"b/{filename}",
        n=context,
    )
    result = "".join(diff)
    
    # 如果 diff 过长，截断并添加提示信息
    if len(result) > 3000:
        result = result[:2500] + "\n... (diff truncated)\n"
    return result
