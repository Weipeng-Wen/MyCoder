<div align="center">

# 🚀 CoreCoder

<p>
  <strong>我的极简 AI 编程 Agent 小实验</strong><br>
  <span style="color:#2563eb">把一个 coding agent 拆开看看：它到底是怎么读代码、调工具、改文件、继续对话的。</span>
</p>

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![Version](https://img.shields.io/badge/CoreCoder-0.4.0-22c55e)
![License](https://img.shields.io/badge/License-MIT-f59e0b)
![Agent](https://img.shields.io/badge/AI-Coding_Agent-8b5cf6)

</div>

---

## 🧡 这个项目是干嘛的

这是我自己改的一个私人项目，主要用来学习和折腾 AI Coding Agent。

它不是那种包装得很满的“正式产品”，更像是一个能跑起来的源码笔记。我想看清楚一个编程 Agent 最核心的几件事：

| 我关心的问题 | CoreCoder 里对应的部分 |
|---|---|
| 🧠 模型怎么决定下一步？ | `agent.py` 里的主循环 |
| 🧰 模型怎么真正动手？ | `tools/` 里的各种工具 |
| 📚 对话太长怎么办？ | `context.py` 的上下文压缩 |
| 💬 怎么在终端里聊天？ | `cli.py` 的 REPL |
| 🔌 怎么换不同模型？ | `llm.py` 和 `config.py` |
| 💾 怎么保存一次任务？ | `session.py` |

简单说：  
<span style="color:#7c3aed"><strong>CoreCoder = LLM + 工具调用 + 上下文管理 + 终端交互。</strong></span>

---

## 🧭 文件夹大概长这样

```text
corecoder/
├── agent.py              # Agent 主循环
├── cli.py                # 终端交互入口
├── config.py             # 配置读取
├── context.py            # 上下文压缩
├── llm.py                # 模型接口
├── prompt.py             # 系统提示词
├── session.py            # 会话保存/恢复
├── __init__.py           # 包导出
├── __main__.py           # python -m corecoder 入口
└── tools/
    ├── __init__.py       # 工具注册
    ├── base.py           # 工具基类
    ├── bash.py           # 执行命令
    ├── read.py           # 读文件
    ├── write.py          # 写文件
    ├── edit.py           # 改文件
    ├── glob_tool.py      # 找文件
    ├── grep.py           # 搜内容
    ├── agent.py          # 子 Agent
    └── now_time.py       # 当前时间
```

> `__pycache__/` 是 Python 自动生成的缓存，不用管。

---

## ⚡ 我怎么跑它

### 1. 安装

```bash
pip install -e .
```

### 2. 配置 API Key

可以放到 `.env`，也可以直接设置环境变量。

| 模型来源 | 配置示例 |
|---|---|
| OpenAI 兼容接口 | `OPENAI_API_KEY=sk-...` |
| DeepSeek | `OPENAI_API_KEY=sk-... OPENAI_BASE_URL=https://api.deepseek.com CORECODER_MODEL=deepseek-chat` |
| 本地 Ollama | `OPENAI_API_KEY=ollama OPENAI_BASE_URL=http://localhost:11434/v1 CORECODER_MODEL=qwen2.5-coder` |
| LiteLLM | `CORECODER_PROVIDER=litellm CORECODER_MODEL=anthropic/claude-3-haiku` |

### 3. 启动

```bash
corecoder
```

或者一次性问一句：

```bash
corecoder -p "帮我看一下这个项目的入口在哪里"
```

---

## 🐍 每个 `.py` 文件是干嘛的

### 核心文件

| 文件 | 作用 | 我觉得值得看的点 |
|---|---|---|
| `corecoder/agent.py` | 整个 Agent 的大脑。用户输入进来后，它负责问模型、执行工具、把工具结果继续交给模型。 | <span style="color:#7c3aed">主循环很直观：LLM 返回工具调用就执行，没有工具调用就结束回答。</span> |
| `corecoder/cli.py` | 命令行界面。包括交互式聊天、一次性 prompt、帮助命令、保存会话、查看 token 等。 | <span style="color:#2563eb">这个文件能看到一个终端 Agent 怎么从“能跑”变成“能用”。</span> |
| `corecoder/config.py` | 从环境变量和 `.env` 里读配置，比如模型名、API Key、base URL、上下文大小等。 | <span style="color:#059669">兼容几种常见 API Key 名称，换模型比较方便。</span> |
| `corecoder/context.py` | 管理上下文长度。对话太长、工具输出太多时，它会做压缩。 | <span style="color:#dc2626">三层压缩挺有意思：先裁剪，再总结，最后硬折叠。</span> |
| `corecoder/llm.py` | 和大模型通信。支持 OpenAI 兼容接口，也支持 LiteLLM。 | <span style="color:#ea580c">这里处理了流式输出、工具调用解析、重试、token 统计和费用估算。</span> |
| `corecoder/prompt.py` | 生成系统提示词。会把当前目录、系统信息、Python 版本、工具列表塞进去。 | <span style="color:#9333ea">提示词不是写死的，会根据运行环境动态生成。</span> |
| `corecoder/session.py` | 保存、恢复、列出历史会话。 | <span style="color:#0891b2">有 session id 清洗和路径检查，避免乱读乱写。</span> |
| `corecoder/__init__.py` | 包入口导出。 | <span style="color:#16a34a">方便外部直接导入 `Agent`、`LLM`、`Config`、`ALL_TOOLS`。</span> |
| `corecoder/__main__.py` | 支持 `python -m corecoder`。 | <span style="color:#475569">很小，但让启动方式更完整。</span> |

### 工具文件

| 文件 | 作用 | 我觉得值得看的点 |
|---|---|---|
| `corecoder/tools/__init__.py` | 把所有工具注册到 `ALL_TOOLS`。 | <span style="color:#059669">以后加新工具，基本就在这里挂一下。</span> |
| `corecoder/tools/base.py` | 工具基类。规定工具要有名字、描述、参数 schema 和执行方法。 | <span style="color:#7c3aed">能自动转成 OpenAI function calling 需要的 schema。</span> |
| `corecoder/tools/bash.py` | 执行 shell 命令。 | <span style="color:#dc2626">有危险命令拦截、超时、输出截断、cwd 跟踪。</span> |
| `corecoder/tools/read.py` | 读取文件内容，并带上行号。 | <span style="color:#2563eb">带行号对模型很友好，后面改代码更容易定位。</span> |
| `corecoder/tools/write.py` | 新建文件或完整覆盖文件。 | <span style="color:#ea580c">写完会记录到 `_changed_files`，可以配合 `/diff` 看改过什么。</span> |
| `corecoder/tools/edit.py` | 精准替换文件中的一段文本。 | <span style="color:#16a34a">只有 `old_string` 唯一匹配时才改，还会返回 diff。</span> |
| `corecoder/tools/glob_tool.py` | 根据 glob 模式找文件。 | <span style="color:#0891b2">按修改时间排序，最近动过的文件会靠前。</span> |
| `corecoder/tools/grep.py` | 用正则搜索文件内容。 | <span style="color:#9333ea">会跳过 `.git`、`node_modules`、虚拟环境、构建目录这些噪声。</span> |
| `corecoder/tools/agent.py` | 派一个子 Agent 去处理复杂子任务。 | <span style="color:#db2777">子 Agent 有独立上下文，但不会再继续派子 Agent，避免递归套娃。</span> |
| `corecoder/tools/now_time.py` | 获取当前时间。 | <span style="color:#475569">时间这种会变的信息，还是让工具实时拿比较靠谱。</span> |

---

## 🧰 Tools 作用和创新点

| Tool | 它能干嘛 | 创新点 / 小心思 |
|---|---|---|
| 🖥️ `bash` | 跑命令、跑测试、看环境、做 git 操作。 | <span style="color:#dc2626">不是无脑执行：先检查危险命令，执行时有 timeout，输出太长也会截断。</span> |
| 📖 `read_file` | 读文件。 | <span style="color:#2563eb">输出自带行号，适合模型按位置理解代码。</span> |
| 📝 `write_file` | 写新文件或重写整个文件。 | <span style="color:#ea580c">会自动创建父目录，也会记录这个文件被改过。</span> |
| ✂️ `edit_file` | 对已有文件做小范围替换。 | <span style="color:#16a34a">要求旧文本只出现一次，这样不容易误伤别的地方。</span> |
| 🔎 `glob` | 按文件名规则找文件。 | <span style="color:#0891b2">支持 `**/*.py` 这种递归匹配，还会优先显示最近修改的文件。</span> |
| 🔍 `grep` | 搜代码里的内容。 | <span style="color:#9333ea">带目录过滤和结果上限，避免搜出一大堆没用内容。</span> |
| 🤖 `agent` | 让子 Agent 单独处理一个任务。 | <span style="color:#db2777">适合把“先调查一下代码结构”这种任务隔离出去，主对话不会被塞爆。</span> |
| ⏰ `now_time` | 获取当前系统时间。 | <span style="color:#475569">让模型别猜时间，直接查。</span> |

---

## 🧠 它的核心流程

我理解下来，CoreCoder 的主流程其实就是这个：

```text
用户说一句话
  ↓
把系统提示词 + 历史对话交给 LLM
  ↓
LLM 判断：要不要调用工具？
  ├─ 不需要：直接回答
  └─ 需要：执行工具，把结果放回对话，再问 LLM
```

看起来简单，但真正能跑起来，靠的是这些细节：

| 细节 | 作用 |
|---|---|
| 工具参数先校验 | 模型传错参数时，不至于直接崩 |
| 多个工具并发执行 | 模型一次调多个工具时更快 |
| 每轮都检查上下文 | 对话长了自动压缩 |
| 工具结果回填 messages | 让模型知道刚才工具执行了什么 |
| 最大轮数限制 | 防止模型一直调工具停不下来 |

---

## 🪟 上下文压缩

`context.py` 这一块我觉得挺值得看。它不是等爆了才处理，而是分阶段压缩：

| 阶段 | 触发点 | 怎么处理 |
|---|---:|---|
| 1️⃣ 裁剪工具输出 | 约 50% 上下文 | 长日志只留开头和结尾 |
| 2️⃣ 总结旧对话 | 约 70% 上下文 | 用 LLM 总结旧内容，保留最近几条 |
| 3️⃣ 硬折叠 | 约 90% 上下文 | 只保留摘要和最近消息 |

还有一个细节：它会尽量避免把 tool call 和 tool result 拆开。  
不然模型接口可能会觉得消息格式不合法。

---

## 💬 终端里能用的命令

| 命令 | 用途 |
|---|---|
| `/help` | 看帮助 |
| `/reset` | 清空当前对话 |
| `/model` | 查看当前模型 |
| `/model <name>` | 临时切换模型 |
| `/tokens` | 看 token 用量和估算费用 |
| `/compact` | 手动压缩上下文 |
| `/diff` | 看这次会话改过哪些文件 |
| `/save` | 保存会话 |
| `/sessions` | 查看保存过的会话 |
| `quit` / `exit` | 退出 |

---

## 🔐 我比较喜欢的安全设计

| 位置 | 做了什么 | 为什么有用 |
|---|---|---|
| `bash.py` | 拦截一些明显危险命令 | 防止模型误执行破坏性操作 |
| `edit.py` | 旧文本必须唯一匹配 | 避免一改改一片 |
| `edit.py` | 返回 diff | 改了什么一眼能看到 |
| `session.py` | 清洗 session id | 避免路径穿越 |
| `agent.py` | 限制最大工具调用轮数 | 防止无限循环 |
| `context.py` | 安全切分消息 | 防止 tool call/result 对不上 |

---

## 🌱 后面可以继续折腾的方向

| 想法 | 可以改哪里 |
|---|---|
| 加一个真正的权限确认机制 | `tools/bash.py`、`tools/write.py`、`tools/edit.py` |
| 给工具加更细的沙箱 | `tools/base.py` 和各个工具 |
| 做一个 Web UI | 新增前端，复用 `Agent` |
| 增加项目索引能力 | 新增 indexing / retrieval 工具 |
| 把上下文压缩做得更聪明 | `context.py` |
| 加插件式工具加载 | `tools/__init__.py` |

---

## 🧪 一句话总结

<div align="center">

<strong>CoreCoder 对我来说不是一个“包装好的成品”，而是一个能拆、能跑、能改的 Agent 学习底座。</strong><br>
<span style="color:#2563eb">越读越能感觉到：coding agent 的核心并不神秘，难的是把每个边界处理稳。</span>

</div>
