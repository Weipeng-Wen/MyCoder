"""
会话管理 - 保存和恢复对话。
- Claude Code通过QueryEngine(1295行)维护会话状态。
- CoreCoder将其简化为: 消息+模型配置的JSON转储。
"""

import json  # JSON格式
import re  # 正则化
import time  # 时间戳
import uuid  # UUID生成
from pathlib import Path  # 路径

SESSIONS_DIR = Path.home() / ".corecoder" / "sessions"  # 会话文件存储目录
_SAFE_SESSION_RE = re.compile(r"[^A-Za-z0-9._-]+")  # 安全的会话ID字符正则表达式
_MAX_SESSION_ID_LEN = 100  # 最长会话ID长度


def _normalize_session_id(session_id: str | None) -> str:
    """规范化会话ID"""

    # 如果没有提供会话ID,则生成一个新的会话ID
    if not session_id:
        return _new_session_id()

    # 将会话ID中的反斜杠替换为正斜杠,并获取最后一个路径组件作为会话名称
    name = session_id.strip().replace("\\", "/").split("/")[-1]

    # 使用正则表达式替换不安全的字符为"-",并去除开头和结尾的".", "-", "_"字符
    name = _SAFE_SESSION_RE.sub("-", name).strip(".-_")

    # 如果会话名称超过最大长度,则截断并去除开头和结尾的".", "-", "_"字符
    if len(name) > _MAX_SESSION_ID_LEN:
        name = name[:_MAX_SESSION_ID_LEN].strip(".-_")

    return name or _new_session_id()


def _new_session_id() -> str:
    """用时间戳生成新的会话ID"""
    return f"session_{time.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"


def _session_path(session_id: str) -> Path:
    """第二道防线: 检查会话ID是否安全,防止路径遍历攻击"""

    # 判断父路径是否为SESSIONS_DIR,如果不是,则抛出ValueError异常,防止路径遍历攻击。
    path = (SESSIONS_DIR / f"{_normalize_session_id(session_id)}.json").resolve()
    root = SESSIONS_DIR.resolve()
    if root != path.parent:
        raise ValueError("Invalid session id")
    return path


def save_session(messages: list[dict], model: str, session_id: str | None = None) -> str:
    """保存会话,返回会话ID。"""

    # 创建会话目录,如果不存在则创建父目录
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

    # 规范化会话ID,如果没有提供会话ID,则生成一个新的会话ID
    session_id = _normalize_session_id(session_id)

    data = {
        "id": session_id,
        "model": model,
        "saved_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "messages": messages,
    }

    # 获取会话文件路径
    path = _session_path(session_id)

    # 将数据写入文件,使用UTF-8编码,并确保非ASCII字符不被转义,缩进为2个空格。
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return session_id


def load_session(session_id: str) -> tuple[list[dict], str] | None:
    """加载会话,返回消息列表和模型配置,如果会话不存在或损坏则返回None。"""

    # 获取会话文件路径
    path = _session_path(session_id)
    if not path.exists():
        return None

    try:
        # 读取会话文件内容,使用UTF-8编码,并解析为JSON对象,返回消息列表和模型配置。
        data = json.loads(path.read_text(encoding="utf-8"))
        return data["messages"], data["model"]
    
    except (json.JSONDecodeError, KeyError, OSError):
        # 如果会话文件损坏或无法读取,则返回None
        return None


def list_sessions() -> list[dict]:
    """列举所有会话,返回会话ID、模型配置、保存时间和预览信息的列表。"""

    # 如果会话目录不存在,则返回空列表
    if not SESSIONS_DIR.exists():
        return []

    sessions = []
    # 遍历会话目录下的所有JSON文件,按修改时间倒序排序,最多返回20个会话。
    for f in sorted(SESSIONS_DIR.glob("*.json"), reverse=True):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))

            # 获取第一个用户消息作为预览,如果没有用户消息则为空字符串
            preview = ""
            for m in data.get("messages", []):
                if m.get("role") == "user" and m.get("content"):
                    preview = m["content"][:80]
                    break
            
            # 将会话信息添加到列表中,包括会话ID、模型配置、保存时间和预览信息。
            sessions.append({
                "id": data.get("id", f.stem),
                "model": data.get("model", "?"),
                "saved_at": data.get("saved_at", "?"),
                "preview": preview,
            })
        except (json.JSONDecodeError, KeyError):
            continue

    # 返回最多20个会话,以防止列表过长影响性能
    return sessions[:20]
