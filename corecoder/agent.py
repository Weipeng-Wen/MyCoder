"""Core agent loop.

This is the heart of CoreCoder.  The pattern is simple:

    user message -> LLM (with tools) -> tool calls? -> execute -> loop
                                      -> text reply? -> return to user

It keeps looping until the LLM responds with plain text (no tool calls),
which means it's done working and ready to report back.
"""

import concurrent.futures  # 并发编程
import inspect  # 检查函数签名
from .llm import LLM  # 大语言模型
from .tools import ALL_TOOLS  # 所有可用工具
from .tools.base import Tool  # 基础工具
from .tools.agent import AgentTool  # 子Agent工具
from .prompt import system_prompt  # 系统提示词
from .context import ContextManager  # 上下文管理器


class Agent:
    """
    CoreCoder的核心模块,负责处理用户输入、调用大语言模型(LLM)和工具,并管理对话历史和上下文。
    """
    def __init__(
        self,
        llm: LLM,  # 大语言模型实例,用于生成响应和调用工具。
        tools: list[Tool] | None = None,  # 可选的工具列表,如果未提供,将使用ALL_TOOLS中的所有工具。
        max_context_tokens: int = 128_000,  # 上下文管理器中允许的最大令牌数,用于控制对话历史的长度和复杂性。
        max_rounds: int = 50,  # 最大循环轮数,用于限制在处理用户输入时的最大迭代次数,防止无限循环。
    ):
        self.llm = llm
        self.tools = tools if tools is not None else ALL_TOOLS
        self._tool_by_name = {t.name: t for t in self.tools}  # 获取所有工具的字典,键为工具名称,值为工具实例,用于快速查找和调用工具。
        self.messages: list[dict] = []  # 用于存储对话历史的消息列表,每条消息是一个字典,包含角色和内容。
        self.context = ContextManager(max_tokens=max_context_tokens)  # 上下文管理器实例,用于管理对话历史和上下文信息,确保不会超过最大令牌数。
        self.max_rounds = max_rounds
        self._system = system_prompt(self.tools)  # 将获取的工具列表传递给system_prompt函数,生成系统提示词,用于指导大语言模型的行为和响应。

        # 让AgentTool知道它的父Agent,以便在执行子任务时可以访问父Agent的上下文和工具。
        for t in self.tools:
            if isinstance(t, AgentTool):
                t._parent_agent = self

    def _full_messages(self) -> list[dict]:
        """拼接系统提示词和对话历史,返回完整的消息列表,用于传递给大语言模型进行处理。"""
        return [{"role": "system", "content": self._system}] + self.messages

    def _tool_schemas(self) -> list[dict]:
        """返回所有工具的JSON Schema列表,用于传递给大语言模型进行工具调用。"""
        return [t.schema() for t in self.tools]

    def chat(self, user_input: str, on_token=None, on_tool=None) -> str:
        """输入用户消息,返回大语言模型的响应文本,并处理工具调用和执行。"""

        self.messages.append({"role": "user", "content": user_input})  # 将用户输入添加到消息列表中,角色为"user",内容为用户输入的文本。
        self.context.maybe_compress(self.messages, self.llm)  # 检查消息列表的长度和复杂性,如果超过最大令牌数,则进行压缩处理,以确保不会超过上下文管理器的限制。

        for _ in range(self.max_rounds):  # 循环处理大语言模型的响应和工具调用,最多进行max_rounds轮迭代,防止无限循环。
            resp = self.llm.chat(
                messages=self._full_messages(),  # 获取完整的消息列表,包括系统提示词和对话历史,传递给大语言模型进行处理。
                tools=self._tool_schemas(),  # 获取所有工具的JSON Schema列表,传递给大语言模型进行工具调用。
                on_token=on_token,  # 
            )

            # 如果大语言模型的响应中没有工具调用,则将响应消息添加到消息列表中,并返回响应内容。
            if not resp.tool_calls:
                self.messages.append(resp.message)  # 格式一般是 {"role": "assistant", "content": "..."}
                return resp.content

            # 如果大语言模型的响应中包含工具调用,则将响应消息添加到消息列表中,并尝试执行工具调用。
            self.messages.append(resp.message)  # 格式一般是 {"role": "assistant", "content": "...", "tool_calls": [...]}

            try:
                # 如果只有一个工具调用,则直接执行该工具调用,并将结果添加到消息列表中。
                if len(resp.tool_calls) == 1:
                    tc = resp.tool_calls[0]  # 获取第一个工具调用对象,包含工具名称、参数和调用ID等信息。
                    # 如果提供了on_tool回调函数
                    if on_tool:
                        on_tool(tc.name, tc.arguments)
                    result = self._exec_tool(tc)  # 执行工具调用,返回执行结果字符串。
                    self.messages.append({  # 添加工具调用结果到消息列表中,角色为"tool",包含工具调用ID和执行结果内容。
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result,
                    })

                # 如果有多个工具调用,则使用线程池并行执行所有工具调用,并将结果添加到消息列表中。
                else:
                    results = self._exec_tools_parallel(resp.tool_calls, on_tool)  # 并行执行多个工具调用,返回每个工具调用的执行结果列表。
                    for tc, result in zip(resp.tool_calls, results):  # 将每个工具调用对象和对应的执行结果进行配对,并将结果添加到消息列表中。
                        self.messages.append({
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": result,
                        })
            except KeyboardInterrupt:
                # 如果在执行工具调用过程中收到键盘中断信号(如Ctrl+C),则调用_answer_pending_tool_calls方法
                # 为所有未完成的工具调用添加一个"[interrupted]"的占位符回复,以保持消息列表的完整性和一致性。
                self._answer_pending_tool_calls(resp.tool_calls)
                raise

            # 在每轮循环结束后,再次检查消息列表的长度和复杂性,如果超过最大令牌数,则进行压缩处理,以确保不会超过上下文管理器的限制。
            self.context.maybe_compress(self.messages, self.llm)

        return "(reached maximum tool-call rounds)"

    def _exec_tool(self, tc) -> str:
        """执行单个工具调用,返回执行结果字符串。"""

        tool = self._tool_by_name.get(tc.name)
        if tool is None:
            return f"Error: unknown tool '{tc.name}'"

        # 两段式检测，区分是参数错误还是工具执行错误
        # 先检查参数是否符合工具的参数要求,如果不符合,则返回错误信息。
        try:
            inspect.signature(tool.execute).bind(**tc.arguments)  # 不会执行函数,只是检查参数是否匹配,如果不匹配,则抛出TypeError异常。
        except TypeError as e:
            return f"Error: bad arguments for {tc.name}: {e}"
        
        # 执行工具调用,如果执行过程中发生异常,则返回错误信息。
        try:
            return tool.execute(**tc.arguments)
        except Exception as e:
            return f"Error executing {tc.name}: {e}"

    def _exec_tools_parallel(self, tool_calls, on_tool=None) -> list[str]:
        """并行执行多个工具调用,返回每个工具调用的执行结果列表。"""

        for tc in tool_calls:
            if on_tool:
                on_tool(tc.name, tc.arguments)

        # 使用线程池并行执行工具调用,提高执行效率,尤其是在有多个耗时的工具调用时。
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            futures = [pool.submit(self._exec_tool, tc) for tc in tool_calls]
            return [f.result() for f in futures]

    def _answer_pending_tool_calls(self, tool_calls):
        """为所有未完成的工具调用添加一个"[interrupted]"的占位符回复,以保持消息列表的完整性和一致性。"""

        # 获取消息列表中所有已经回答过的工具调用ID集合,用于判断哪些工具调用已经有回复,避免重复添加占位符回复。
        answered = {m.get("tool_call_id") for m in self.messages if m.get("role") == "tool"}
        for tc in tool_calls:
            if tc.id not in answered:
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": "[interrupted]",
                })

    def reset(self):
        """清空对话历史和上下文,用于重新开始一个新的对话。"""
        self.messages.clear()
