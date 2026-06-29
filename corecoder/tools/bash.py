"""对执行的 Bash 命令进行安全检查，防止破坏性操作或泄露敏感信息。"""

import os  # 操作系统路径
import re  # 正则化
import subprocess  # 执行子进程
import threading  # 线程本地存储
from .base import Tool  # 工具父类

# 线程本地存储，用于跟踪每个线程的工作目录（让每个线程独立地维护自己的工作目录状态，互不影响）
_local = threading.local()

# 可能破坏文件系统或泄露机密的模式
_DANGEROUS_PATTERNS = [
    # 针对 root/home 的递归删除（强制标志可选）
    (r"\brm\s+(-\w*)?-r\w*\s+(/|~|\$HOME)", "recursive delete on home/root"),

    # 递归 (-r/-R) 和强制 (-f) 标志一起使用，顺序或间距不限
    (r"\brm\b(?=(?:.*\s)?-\w*[rR])(?=(?:.*\s)?-\w*f)", "force recursive delete"),

    # 相同的模式，但使用长格式标志
    (r"\brm\b.*--recursive\b.*--force\b|\brm\b.*--force\b.*--recursive\b", "force recursive delete"),
    (r"\bmkfs\b", "format filesystem"),
    (r"\bdd\s+.*of=/dev/", "raw disk write"),
    (r">\s*/dev/sd[a-z]", "overwrite block device"),
    (r"\bchmod\s+(-R\s+)?777\s+/", "chmod 777 on root"),
    (r":\(\)\s*\{.*:\|:.*\}", "fork bomb"),
    (r"\bcurl\b.*\|\s*(sudo\s+)?(ba)?sh\b", "pipe curl to shell"),
    (r"\bwget\b.*\|\s*(sudo\s+)?(ba)?sh\b", "pipe wget to shell"),
]


class BashTool(Tool):
    """执行Bash命令的工具。返回stdout、stderr和退出代码。用于运行测试、安装软件包、git操作等。"""

    name = "bash"
    description = (
        "Execute a shell command. Returns stdout, stderr, and exit code. "
        "Use this for running tests, installing packages, git operations, etc."
    )
    parameters = {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The shell command to run",
            },
            "timeout": {
                "type": "integer",
                "description": "Timeout in seconds (default 120)",
            },
        },
        "required": ["command"],
    }

    def execute(self, command: str, timeout: int = 120) -> str:
        # 安全检查：阻止破坏性命令或泄露敏感信息
        warning = _check_dangerous(command)
        if warning:
            return f"⚠ Blocked: {warning}\nCommand: {command}\nIf intentional, modify the command to be more specific."

        # 获取当前线程的工作目录，如果没有设置，则使用当前工作目录（cwd是当前工作目录的缩写）
        cwd = getattr(_local, "cwd", None) or os.getcwd()

        try:
            # 执行命令，捕获输出和错误
            proc = subprocess.run(
                command,  # 要执行的命令
                shell=True,  # 使用shell执行命令
                capture_output=True,  # 捕获stdout和stderr
                text=True,  # 将输出作为文本处理
                encoding="utf-8",  # 使用UTF-8编码
                errors="replace",  # 错误处理策略，替换无法解码的字符
                timeout=timeout,  # 超时设置
                cwd=cwd,  # 设置命令执行的工作目录
            )

            # 跟踪目录变化，如果命令中有cd操作，则更新当前工作目录
            if proc.returncode == 0:
                _update_cwd(command, cwd)
            
            # 获取标准输出
            out = proc.stdout

            # 如果有错误输出，则将其附加到输出中
            if proc.stderr:
                out += f"\n[stderr]\n{proc.stderr}"

            # 如果命令返回非零退出代码，则在输出中添加退出代码信息
            if proc.returncode != 0:
                out += f"\n[exit code: {proc.returncode}]"
            
            # 如果输出过长，则截断输出，保留前6000个字符和后3000个字符，并在中间添加截断提示
            if len(out) > 15_000:
                out = (
                    out[:6000]
                    + f"\n\n... truncated ({len(out)} chars total) ...\n\n"
                    + out[-3000:]
                )
            return out.strip() or "(no output)"
        
        # 处理命令执行超时异常
        except subprocess.TimeoutExpired:
            return f"Error: timed out after {timeout}s"
        
        # 处理其他异常，返回错误信息
        except Exception as e:
            return f"Error running command: {e}"


def _check_dangerous(cmd: str) -> str | None:
    """检查命令是否包含潜在危险的模式。如果检测到危险模式，则返回警告信息，否则返回None。"""
    for pattern, reason in _DANGEROUS_PATTERNS:
        if re.search(pattern, cmd):
            return reason
    return None


def _update_cwd(command: str, current_cwd: str):
    """更新当前线程的工作目录，如果命令中包含cd操作，则将工作目录更改为指定的路径。"""

    # 获取当前线程的工作目录，如果没有设置，则使用传入的current_cwd
    running = current_cwd
    changed = False

    # 解析命令中的每个部分，查找cd操作
    for part in command.split("&&"):
        part = part.strip()
        # 如果命令部分以cd开头，则尝试更改工作目录
        if part.startswith("cd "):
            target = part[3:].strip().strip("'\"")
            # 将目标路径与当前工作目录结合，规范化路径，并检查是否为有效目录
            if target:
                new_dir = os.path.normpath(os.path.join(running, os.path.expanduser(target)))
                if os.path.isdir(new_dir):
                    running = new_dir
                    changed = True
    
    # 如果工作目录发生了变化，则更新线程本地存储中的cwd属性
    if changed:
        _local.cwd = running