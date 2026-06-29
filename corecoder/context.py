"""多层上下文压缩。
Claude Code 使用了四层策略：
  1. HISTORY_SNIP   - 将旧的工具输出修剪为一行摘要
  2. Microcompact   - 使用 LLM 对旧的对话进行总结
  3. CONTEXT_COLLAPSE - 当接近硬限制时进行激进的压缩
  4. Autocompact    - 定期的后台压缩
CoreCoder 实现了相同的想法，但只有三层：
  层 1 (tool_snip)   - 用截断版本替换冗长的工具结果
  层 2 (summarize)   - 使用 LLM 对旧的对话进行总结
  层 3 (hard_collapse) - 最后的手段：丢弃除摘要和最近消息之外的所有内容
"""

from __future__ import annotations
from typing import TYPE_CHECKING  # 解决循环导入问题

if TYPE_CHECKING:
    from .llm import LLM


def _approx_tokens(text: str) -> int:
    """
    简单的Token计数器。每3个字符大约1个token,这不是精确的,但足够用于估计上下文大小。
    正常是用tokenizer来计算的,但我们不想在这里引入依赖。
    """
    return len(text) // 3


def estimate_tokens(messages: list[dict]) -> int:
    """估计消息列表的token数量。"""
    total = 0
    for m in messages:
        if m.get("content"):
            total += _approx_tokens(m["content"])
        if m.get("tool_calls"):
            total += _approx_tokens(str(m["tool_calls"]))
    return total


class ContextManager:
    def __init__(self, max_tokens: int = 128_000):
        self.max_tokens = max_tokens  # 最大上下文大小
        
        # 三重阈值：当消息列表超过这些阈值时，应用不同的压缩策略
        self._snip_at = int(max_tokens * 0.50)    # 50% -> 直接截断冗长的工具输出
        self._summarize_at = int(max_tokens * 0.70)  # 70% -> 用LLM总结旧的对话，保留最近的消息
        self._collapse_at = int(max_tokens * 0.90)   # 90% -> 紧急压缩，丢弃旧的对话，只保留摘要和最近的消息（一般用不上，因为前两个策略足够了）

    def maybe_compress(self, messages: list[dict], llm: LLM | None = None) -> bool:
        """判断是否需要压缩上下文，并在必要时进行压缩。"""
        current = estimate_tokens(messages)
        compressed = False

        # 第一层: 截断冗长的工具输出
        if current > self._snip_at:
            if self._snip_tool_outputs(messages):
                compressed = True
                current = estimate_tokens(messages)

        # 第二层: 用LLM总结旧的对话
        if current > self._summarize_at and len(messages) > 10:
            if self._summarize_old(messages, llm, keep_recent=8):
                compressed = True
                current = estimate_tokens(messages)

        # 第三层: 紧急压缩 - 最后的手段
        if current > self._collapse_at and len(messages) > 4:
            self._hard_collapse(messages, llm)
            compressed = True

        return compressed

    @staticmethod
    def _snip_tool_outputs(messages: list[dict]) -> bool:
        """第一层: 将超过1500个字符的工具输出截断为其前几行和后几行。"""

        changed = False
        # 遍历消息列表，查找工具输出
        for m in messages:

            # 只处理工具输出消息
            if m.get("role") != "tool":
                continue

            # 获取工具输出内容，如果内容长度未超过1500个字符，则跳过
            content = m.get("content", "")
            if len(content) <= 1500:
                continue

            # 将内容按行分割，并检查行数是否超过6行，未超过则跳过
            lines = content.splitlines()
            if len(lines) <= 6:
                continue

            # 保留前3行和后3行，并在中间插入一条提示，说明内容已被截断
            snipped = (
                "\n".join(lines[:3])
                + f"\n... ({len(lines)} lines, snipped to save context) ...\n"
                + "\n".join(lines[-3:])
            )
            m["content"] = snipped
            changed = True
        return changed

    @staticmethod
    def _safe_split(messages: list[dict], keep_recent: int) -> int:
        """
        安全地拆分消息列表，确保不会将工具调用与其对应的输出消息分开。

        - 一般来, 先是带有ToolCall的AI消息，然后是Tool消息。我们希望在拆分时，不会恰好将二者拆分开。
        因为如果大语言模型只收到Tool消息而没有对应的ToolCall消息，它会认为这是一个非法消息序列而拒绝请求。
        """

        split = max(0, len(messages) - keep_recent)
        while split > 0 and messages[split].get("role") == "tool":
            split -= 1
        return split

    def _summarize_old(self, messages: list[dict], llm: LLM | None,
                       keep_recent: int = 8) -> bool:
        """第二层: 使用LLM对旧的对话进行总结,保留最近的消息(默认为8条)。"""

        if len(messages) <= keep_recent:
            return False

        # 计算拆分点，确保不会将工具调用与其对应的输出消息分开
        split = self._safe_split(messages, keep_recent)
        old = messages[:split]
        tail = messages[split:]

        # 生成旧消息的摘要
        summary = self._get_summary(old, llm)

        # 清空消息序列，并添加摘要和最近的消息
        messages.clear()
        messages.append({
            "role": "user",
            "content": f"[Context compressed - conversation summary]\n{summary}",
        })
        messages.append({  # 模拟助手的确认消息，表示上下文已恢复
            "role": "assistant",
            "content": "Got it, I have the context from our earlier conversation.",
        })
        messages.extend(tail)
        return True

    def _hard_collapse(self, messages: list[dict], llm: LLM | None):
        """第三层: 紧急压缩。只保留最后4条消息 + 摘要."""

        # 计算拆分点，确保不会将工具调用与其对应的输出消息分开
        split = self._safe_split(messages, 4 if len(messages) > 4 else 2)
        tail = messages[split:]
        summary = self._get_summary(messages[:split], llm)

        messages.clear()
        messages.append({
            "role": "user",
            "content": f"[Hard context reset]\n{summary}",
        })
        messages.append({
            "role": "assistant",
            "content": "Context restored. Continuing from where we left off.",
        })
        messages.extend(tail)

    def _get_summary(self, messages: list[dict], llm: LLM | None) -> str:
        """总结旧的对话。尝试使用LLM，如果失败则回退到关键行提取"""

        # 将消息列表展平为单个字符串，以便传递给LLM进行摘要生成
        flat = self._flatten(messages)

        if llm:
            try:
                # 使用LLM生成摘要
                resp = llm.chat(
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "Compress this conversation into a brief summary. "
                                "Preserve: file paths edited, key decisions made, "
                                "errors encountered, current task state. "
                                "Drop: verbose command output, code listings, "
                                "redundant back-and-forth."
                            ),
                        },
                        {"role": "user", "content": flat[:15000]},
                    ],
                )
                return resp.content
            except Exception:
                pass

        # 如果LLM不可用或失败，则回退到关键行提取
        return self._extract_key_info(messages)

    @staticmethod
    def _flatten(messages: list[dict]) -> str:
        """将消息列表展平为单个字符串,用于传递给LLM进行摘要生成。"""
        parts = []
        for m in messages:
            role = m.get("role", "?")
            text = m.get("content", "") or ""
            if text:
                parts.append(f"[{role}] {text[:400]}")
        return "\n".join(parts)


    @staticmethod
    def _extract_key_info(messages: list[dict]) -> str:
        """如果没有LLM或LLM失败,则提取关键行信息作为摘要。"""
        import re
        files_seen = set()
        errors = []

        for m in messages:
            text = m.get("content", "") or ""
            # 提取文件路径
            for match in re.finditer(r'[\w./\-]+\.\w{1,5}', text):
                files_seen.add(match.group())
            # 提取错误行
            for line in text.splitlines():
                if "error" in line.lower():
                    errors.append(line.strip()[:150])

        parts = []
        if files_seen:
            parts.append(f"Files touched: {', '.join(sorted(files_seen)[:20])}")
        if errors:
            parts.append(f"Errors seen: {'; '.join(errors[:5])}")
        return "\n".join(parts) or "(no extractable context)"
