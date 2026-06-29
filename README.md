<div align="center">

# 🚀 CoreCoder

<p>
  <strong>一个极简、可读、可改造的 AI Coding Agent</strong><br>
  <span style="color:#2563eb">用约千行 Python 展示“模型 + 工具 + 上下文 + 会话”的完整 Agent 工作流</span>
</p>

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![Version](https://img.shields.io/badge/CoreCoder-0.4.0-22c55e)
![License](https://img.shields.io/badge/License-MIT-f59e0b)
![Agent](https://img.shields.io/badge/AI-Coding_Agent-8b5cf6)

</div>

---

## ✨ 项目简介

CoreCoder 是一个面向终端的轻量级 AI 编程助手。它把一个 coding agent 的核心机制拆成清晰的几个部分：

| 模块 | 关键词 | 说明 |
|---|---|---|
| 🧠 Agent 主循环 | <span style="color:#7c3aed">规划与执行</span> | 模型决定下一步，是直接回答还是调用工具 |
| 🧰 Tools 工具层 | <span style="color:#059669">真实动手能力</span> | 读文件、写文件、编辑文件、搜索、执行命令、派生子 Agent |
| 🪟 Context 上下文 | <span style="color:#2563eb">长期任务续航</span> | 对长对话和大输出进行分层压缩 |
| 💬 CLI 交互层 | <span style="color:#dc2626">终端体验</span> | 支持 REPL、一次性 prompt、斜杠命令、会话恢复 |
| 🔌 LLM 适配层 | <span style="color:#ea580c">模型可替换</span> | 支持 OpenAI 兼容接口，也可通过 LiteLLM 接入更多模型 |

它的价值不只是“能用”，更在于“能读懂”：代码规模小、模块边界清晰，非常适合学习和二次开发自己的 Agent。

---

## 🧭 目录结构

```text
corecoder/
├── agent.py              # Agent 主循环：模型调用、工具执行、上下文压缩
├── cli.py                # 命令行入口：REPL、斜杠命令、一次性模式
├── config.py             # 环境变量与 .env 配置加载
├── context.py            # 多层上下文压缩策略
├── llm.py                # OpenAI / LiteLLM 模型接口、流式输出、成本统计
├── prompt.py             # 系统提示词生成
├── session.py            # 会话保存、恢复、列表管理
├── __init__.py           # 包导出
├── __main__.py           # python -m corecoder 入口
└── tools/
    ├── __init__.py       # 工具注册表
    ├── base.py           # 工具抽象基类
    ├── bash.py           # Shell 命令执行工具
    ├── read.py           # 文件读取工具
    ├── write.py          # 文件写入工具
    ├── edit.py           # 精准替换编辑工具
    ├── glob_tool.py      # 文件路径匹配工具
    ├── grep.py           # 文件内容搜索工具
    ├── agent.py          # 子 Agent 工具
    └── now_time.py       # 当前时间工具
```

> `__pycache__/` 是 Python 自动生成的缓存目录，不属于核心源码设计。

---

## ⚡ 快速开始

### 1. 安装依赖

```bash
pip install -e .
```

### 2. 配置模型

你可以通过 `.env` 或环境变量配置模型：

| 场景 | 示例 |
|---|---|
| OpenAI 兼容接口 | `OPENAI_API_KEY=sk-...` |
| DeepSeek | `OPENAI_API_KEY=sk-... OPENAI_BASE_URL=https://api.deepseek.com CORECODER_MODEL=deepseek-chat` |
| 本地 Ollama | `OPENAI_API_KEY=ollama OPENAI_BASE_URL=http://localhost:11434/v1 CORECODER_MODEL=qwen2.5-coder` |
| LiteLLM 多厂商 | `CORECODER_PROVIDER=litellm CORECODER_MODEL=anthropic/claude-3-haiku` |

### 3. 启动

```bash
corecoder
```

或一次性执行：

```bash
corecoder -p "帮我检查这个项目的入口文件"
```

---

## 🧩 每个 Python 文件的作用

### 📦 核心包文件

| 文件 | 代码量 | 作用 | 关键设计 |
|---|---:|---|---|
| `corecoder/agent.py` | 129 行 | CoreCoder 的核心 Agent 主循环。接收用户输入，调用 LLM，根据模型返回决定是否执行工具，并把工具结果继续塞回对话。 | <span style="color:#7c3aed">支持单工具直接执行、多工具线程池并发执行、工具参数签名校验、KeyboardInterrupt 后补齐未完成 tool call。</span> |
| `corecoder/cli.py` | 262 行 | 终端用户界面。负责参数解析、REPL 交互、流式输出、斜杠命令和一次性 prompt 模式。 | <span style="color:#2563eb">把 Rich 的展示能力和 prompt_toolkit 的多行输入、历史记录、快捷键结合起来，形成轻量但完整的终端体验。</span> |
| `corecoder/config.py` | 52 行 | 配置中心。从 `.env` 和环境变量读取模型、API Key、base URL、token 限制、provider 等配置。 | <span style="color:#059669">自动向上查找 `.env`，并兼容 `CORECODER_API_KEY`、`OPENAI_API_KEY`、`DEEPSEEK_API_KEY` 等常见变量。</span> |
| `corecoder/context.py` | 191 行 | 上下文管理器。估算 token，并在对话变长时执行分层压缩。 | <span style="color:#dc2626">三层压缩策略：工具输出裁剪、LLM 总结旧对话、硬折叠保留摘要与最近消息。</span> |
| `corecoder/llm.py` | 296 行 | LLM 适配层。封装 OpenAI 兼容接口和 LiteLLM 接口，处理流式 token、工具调用增量解析、重试、用量统计和成本估算。 | <span style="color:#ea580c">统一 OpenAI 与 LiteLLM 的响应结构，让 Agent 层无需关心具体模型提供商。</span> |
| `corecoder/prompt.py` | 26 行 | 系统提示词生成器。动态注入工作目录、系统信息、Python 版本和当前工具列表。 | <span style="color:#9333ea">提示词不是静态文本，而是根据运行环境和工具注册表生成。</span> |
| `corecoder/session.py` | 96 行 | 会话持久化。支持保存、加载、列举历史会话。 | <span style="color:#0891b2">对 session id 做规范化和路径归属检查，防止路径穿越。</span> |
| `corecoder/__init__.py` | 7 行 | 包级导出。暴露 `Agent`、`LLM`、`Config`、`ALL_TOOLS` 和版本号。 | <span style="color:#16a34a">让外部代码可以直接 `from corecoder import Agent` 使用核心能力。</span> |
| `corecoder/__main__.py` | 2 行 | 模块运行入口。支持 `python -m corecoder` 启动 CLI。 | <span style="color:#475569">把包执行行为统一转发到 `corecoder.cli:main`。</span> |

### 🧰 Tools 包文件

| 文件 | 代码量 | 作用 | 关键设计 |
|---|---:|---|---|
| `corecoder/tools/__init__.py` | 26 行 | 工具注册表。集中实例化全部工具，并提供 `get_tool()` 查询函数。 | <span style="color:#059669">Agent 只需要读取 `ALL_TOOLS`，工具扩展点非常直观。</span> |
| `corecoder/tools/base.py` | 20 行 | 工具抽象基类。规定每个工具必须有 `name`、`description`、`parameters` 和 `execute()`。 | <span style="color:#7c3aed">自动把工具描述转换成 OpenAI function calling schema。</span> |
| `corecoder/tools/bash.py` | 120 行 | Shell 命令执行工具。用于运行测试、安装依赖、执行 git 操作等。 | <span style="color:#dc2626">内置危险命令拦截、超时控制、stderr 合并、输出截断和线程本地 cwd 追踪。</span> |
| `corecoder/tools/read.py` | 50 行 | 文件读取工具。带行号读取指定文件，支持 offset 和 limit。 | <span style="color:#2563eb">强制形成“编辑前先读文件”的 Agent 工作习惯，降低误改风险。</span> |
| `corecoder/tools/write.py` | 36 行 | 文件写入工具。创建新文件或完整覆盖文件内容。 | <span style="color:#ea580c">写入后记录变更文件，配合 CLI 的 `/diff` 命令展示本会话修改过的文件。</span> |
| `corecoder/tools/edit.py` | 82 行 | 精准编辑工具。通过 `old_string` 到 `new_string` 的唯一匹配替换来修改文件。 | <span style="color:#16a34a">要求旧文本在文件中只出现一次，并返回 unified diff，兼顾安全性与可审计性。</span> |
| `corecoder/tools/glob_tool.py` | 43 行 | 文件路径匹配工具。支持 `**/*.py` 这类递归 glob。 | <span style="color:#0891b2">按修改时间倒序返回结果，更适合 Agent 优先关注最近活跃文件。</span> |
| `corecoder/tools/grep.py` | 79 行 | 内容搜索工具。用正则搜索文件内容，返回路径、行号和匹配行。 | <span style="color:#9333ea">自动跳过 `.git`、`node_modules`、虚拟环境、构建产物等噪声目录，并设置匹配上限。</span> |
| `corecoder/tools/agent.py` | 42 行 | 子 Agent 工具。为复杂子任务创建独立上下文的子 Agent。 | <span style="color:#db2777">子 Agent 继承父 Agent 的 LLM 与工具能力，但移除 `agent` 工具自身，避免无限递归。</span> |
| `corecoder/tools/now_time.py` | 14 行 | 当前时间工具。返回人类可读的当前日期时间。 | <span style="color:#475569">让模型在需要时间信息时通过工具获取运行时事实，而不是凭上下文猜测。</span> |

---

## 🧰 Tools 作用与创新点总览

| Tool 名称 | 主要用途 | 输入参数 | 输出 | 创新点 |
|---|---|---|---|---|
| 🖥️ `bash` | 执行终端命令、跑测试、查环境、做 git 操作 | `command`, `timeout` | stdout、stderr、exit code | <span style="color:#dc2626">安全正则拦截危险命令；线程本地 cwd 让并行工具调用时目录状态互不污染；长输出自动截断保护上下文。</span> |
| 📖 `read_file` | 查看文件内容 | `file_path`, `offset`, `limit` | 带行号的文本 | <span style="color:#2563eb">以行号方式暴露上下文，方便模型做精确引用和后续编辑。</span> |
| 📝 `write_file` | 新建文件或完整覆盖 | `file_path`, `content` | 写入行数 | <span style="color:#ea580c">自动创建父目录，并把变更写入 `_changed_files`，让会话级变更可追踪。</span> |
| ✂️ `edit_file` | 小范围精准修改 | `file_path`, `old_string`, `new_string` | 编辑结果和 diff | <span style="color:#16a34a">“唯一匹配才允许修改”的机制，比直接覆盖文件更适合 Agent 安全改代码。</span> |
| 🔎 `glob` | 按文件名或路径模式找文件 | `pattern`, `path` | 匹配文件列表 | <span style="color:#0891b2">支持递归匹配并按最近修改排序，帮助 Agent 快速定位活跃区域。</span> |
| 🔍 `grep` | 搜索代码内容 | `pattern`, `path`, `include` | 文件路径、行号、匹配行 | <span style="color:#9333ea">内置噪声目录过滤和结果上限，避免搜索把上下文打爆。</span> |
| 🤖 `agent` | 派生子 Agent 处理复杂任务 | `task` | 子 Agent 总结结果 | <span style="color:#db2777">用独立上下文隔离探索性任务，父 Agent 只接收压缩后的结论。</span> |
| ⏰ `now_time` | 获取当前系统时间 | 无 | `YYYY-MM-DD HH:MM:SS` | <span style="color:#475569">把时间这种动态事实交给工具获取，减少模型幻觉。</span> |

---

## 🧠 Agent 工作流

```text
用户输入
  ↓
Agent.chat()
  ↓
拼接 system prompt + 历史消息
  ↓
LLM 流式响应
  ↓
是否包含 tool_calls？
  ├─ 否：返回最终回答
  └─ 是：执行工具，将结果写回 messages，再继续询问 LLM
```

这个循环是 CoreCoder 的核心。它的关键不在复杂框架，而在几个边界处理：

| 边界 | 处理方式 |
|---|---|
| 工具参数错误 | 使用 `inspect.signature(...).bind()` 在执行前校验 |
| 多工具调用 | 使用 `ThreadPoolExecutor(max_workers=8)` 并发执行 |
| 中断执行 | 为未完成的 tool call 补 `[interrupted]`，保持消息协议完整 |
| 上下文过长 | 每轮前后都调用 `ContextManager.maybe_compress()` |
| 工具不存在 | 返回结构化错误，让模型有机会自我修正 |

---

## 🪟 上下文压缩机制

`corecoder/context.py` 采用三层策略，尽量在保留任务状态的同时减少 token 消耗：

| 层级 | 触发阈值 | 策略 | 适合处理 |
|---|---:|---|---|
| 1️⃣ Tool Snip | 50% | 裁剪超长工具输出，只保留前 3 行和后 3 行 | 测试日志、搜索结果、命令输出 |
| 2️⃣ Summarize | 70% | 调用 LLM 总结旧对话，保留最近 8 条消息 | 长任务、多轮修改 |
| 3️⃣ Hard Collapse | 90% | 最后手段，只保留摘要和最近消息 | 极限上下文压力 |

此外，`_safe_split()` 会避免把 assistant 的 tool call 和对应 tool result 拆散，防止发送给模型的消息序列非法。

---

## 💬 CLI 命令

| 命令 | 作用 |
|---|---|
| `/help` | 查看帮助 |
| `/reset` | 清空当前对话历史 |
| `/model` | 查看当前模型 |
| `/model <name>` | 会话中切换模型 |
| `/tokens` | 查看 prompt / completion token 用量与估算费用 |
| `/compact` | 手动触发上下文压缩 |
| `/diff` | 查看本会话被工具修改过的文件 |
| `/save` | 保存当前会话 |
| `/sessions` | 列出最近保存的会话 |
| `quit` / `exit` | 退出 |

---

## 🔐 安全设计亮点

| 位置 | 安全措施 | 意义 |
|---|---|---|
| `tools/bash.py` | 拦截 `rm -rf`、`mkfs`、`dd of=/dev/...`、`curl | sh` 等危险模式 | 降低 Agent 执行破坏性命令的风险 |
| `tools/edit.py` | `old_string` 必须唯一匹配 | 避免错误替换多个位置 |
| `tools/edit.py` | 返回 unified diff | 修改过程可审计 |
| `session.py` | session id 规范化 + parent 路径校验 | 防止路径穿越 |
| `context.py` | 工具调用消息安全切分 | 避免破坏 LLM 工具调用协议 |
| `agent.py` | 最大轮数 `max_rounds` | 防止无限工具调用循环 |

---

## 🌈 项目亮点

| 亮点 | 说明 |
|---|---|
| 🧱 极简架构 | 没有重型框架，核心逻辑直接可读 |
| 🔌 模型可替换 | OpenAI 兼容接口 + LiteLLM 后端 |
| 🧰 工具可扩展 | 新工具只需继承 `Tool` 并加入 `ALL_TOOLS` |
| 🧠 上下文可续航 | 三层压缩让长任务更稳 |
| 🧾 修改可追踪 | 写入和编辑工具共享 `_changed_files` |
| 🤖 支持子 Agent | 复杂任务可拆给独立上下文处理 |
| 💸 成本可观察 | LLM 层统计 token，并按内置价格表估算费用 |

---

## 🛠️ 如何扩展一个新工具

1. 在 `corecoder/tools/` 下新建一个工具文件。
2. 继承 `Tool`。
3. 声明 `name`、`description`、`parameters`。
4. 实现 `execute()`。
5. 在 `corecoder/tools/__init__.py` 的 `ALL_TOOLS` 中注册。

示例骨架：

```python
from .base import Tool


class MyTool(Tool):
    name = "my_tool"
    description = "Describe what this tool does."
    parameters = {
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Input text"},
        },
        "required": ["text"],
    }

    def execute(self, text: str) -> str:
        return text.upper()
```

---

## 📌 适合谁阅读

| 读者 | 收获 |
|---|---|
| 想学习 Agent 原理的人 | 看清 coding agent 的主循环、工具协议和上下文管理 |
| 想改造自己的 CLI Agent 的开发者 | 直接复用配置、LLM、工具注册、会话管理等模式 |
| 想研究工具调用安全边界的人 | 观察 bash、edit、session 等模块的防护策略 |
| 想做教学项目的人 | 文件短、职责清晰，适合逐文件讲解 |

---

## 📄 License

MIT License

<div align="center">

<strong>CoreCoder = 小而完整的 Agent 内核。</strong><br>
<span style="color:#2563eb">读懂它，然后 fork 出你自己的编程助手。</span>

</div>
