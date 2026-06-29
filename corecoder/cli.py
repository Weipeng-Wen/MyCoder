"""交互式REPL - 用户界面终端接口。"""

import sys  # 系统模块
import os  # 操作系统
import argparse  # 命令行参数解析

from rich.console import Console  # 终端输出美化库
from rich.markdown import Markdown  # 终端输出Markdown格式文本
from rich.panel import Panel  # 终端输出面板
from prompt_toolkit import prompt as pt_prompt  # 终端输入美化库
from prompt_toolkit.history import FileHistory  # 终端输入历史记录
from prompt_toolkit.key_binding import KeyBindings  # 终端输入快捷键绑定

from .agent import Agent  # 智能体
from .llm import LLM, LiteLLM  # 轻量级大语言模型
from .config import Config  # 配置管理
from .session import save_session, load_session, list_sessions  # 会话管理
from . import __version__

console = Console()  # 终端输出实例


def _parse_args():
    """解析命令行参数,返回解析结果。"""

    # 创建命令行参数解析器,设置程序名称和描述信息。
    p = argparse.ArgumentParser(
        prog="corecoder",
        description="Minimal AI coding agent. Works with any OpenAI-compatible LLM.",
    )

    # 添加命令行参数,包括模型名称、API基础URL、API密钥、一次性提示词、恢复会话ID和版本信息。
    p.add_argument("-m", "--model", help="Model name (default: $CORECODER_MODEL or gpt-5.5)")
    p.add_argument("--base-url", help="API base URL (default: $OPENAI_BASE_URL)")
    p.add_argument("--api-key", help="API key (default: $OPENAI_API_KEY)")
    p.add_argument("-p", "--prompt", help="One-shot prompt (non-interactive mode)")
    p.add_argument("-r", "--resume", metavar="ID", help="Resume a saved session")
    p.add_argument("-v", "--version", action="version", version=f"%(prog)s {__version__}")

    # 解析命令行参数,返回解析结果。
    return p.parse_args()


def main():
    args = _parse_args()  # 解析命令行参数,返回解析结果。
    config = Config.from_env()  # 从环境变量中加载配置,返回配置实例。

    # 如果命令行参数中指定了模型名称、API基础URL或API密钥,则覆盖配置实例中的相应属性。
    if args.model:
        config.model = args.model
    if args.base_url:
        config.base_url = args.base_url
    if args.api_key:
        config.api_key = args.api_key

    # 如果未找到API密钥,则打印错误信息并退出程序,提示用户设置环境变量OPENAI_API_KEY、DEEPSEEK_API_KEY或CORECODER_API_KEY。
    if not config.api_key:
        console.print("[red bold]No API key found.[/]")
        console.print(
            "Set one of: OPENAI_API_KEY, DEEPSEEK_API_KEY, or CORECODER_API_KEY\n"
            "\nExamples:\n"
            "  # OpenAI\n"
            "  export OPENAI_API_KEY=sk-...\n"
            "\n"
            "  # DeepSeek\n"
            "  export OPENAI_API_KEY=sk-... OPENAI_BASE_URL=https://api.deepseek.com\n"
            "\n"
            "  # Ollama (local)\n"
            "  export OPENAI_API_KEY=ollama OPENAI_BASE_URL=http://localhost:11434/v1 CORECODER_MODEL=qwen2.5-coder\n"
        )
        sys.exit(1)

    # 命令行是否指定了模型提供商,如果指定了"litellm",则使用LiteLLM类,否则使用LLM类。
    llm_cls = LiteLLM if config.provider == "litellm" else LLM
    llm = llm_cls(
        model=config.model,
        api_key=config.api_key,
        base_url=config.base_url,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
    )
    agent = Agent(llm=llm, max_context_tokens=config.max_context_tokens)

    # 恢复会话,如果命令行参数中指定了恢复会话ID,则尝试从磁盘加载该会话,并恢复对话历史和模型状态。
    if args.resume:

        # 加载指定会话
        loaded = load_session(args.resume)
        if loaded:
            agent.messages, loaded_model = loaded
            
            # 如果命令行参数中未指定模型名称,则使用加载的会话中的模型名称,并更新配置实例中的模型属性。
            if not args.model:
                agent.llm.model = loaded_model
                config.model = loaded_model
            console.print(f"[green]Resumed session: {args.resume} (model: {agent.llm.model})[/green]")
        else:
            console.print(f"[red]Session '{args.resume}' not found.[/red]")
            sys.exit(1)

    # 如果命令行参数中指定了一次性提示词,则调用_run_once函数处理该提示词,并退出程序。
    if args.prompt:
        _run_once(agent, args.prompt)
        return

    # 交互式REPL,调用_repl函数启动交互式会话,传入智能体实例和配置实例。
    _repl(agent, config)


def _run_once(agent: Agent, prompt: str):
    """无交互模式,处理一次性提示词并输出结果。"""
    def on_token(tok):
        print(tok, end="", flush=True)

    def on_tool(name, kwargs):
        console.print(f"\n[dim]> {name}({_brief(kwargs)})[/dim]")

    # 调用智能体的chat方法处理提示词,传入on_token和on_tool回调函数,用于处理流式输出和工具调用。
    try:
        agent.chat(prompt, on_token=on_token, on_tool=on_tool)
    except KeyboardInterrupt:  # 按下Ctrl+C中断执行,打印中断信息并退出程序,返回码为130。
        console.print("\n[yellow]Interrupted.[/yellow]")
        sys.exit(130)
    except Exception as e:  # 其他异常,打印错误信息并退出程序,返回码为1。
        console.print(f"\n[red]Error: {e}[/red]")
        sys.exit(1)
    print()


def _repl(agent: Agent, config: Config):
    """交互式REPL,处理用户输入并与智能体进行对话。"""

    # 打印欢迎信息,包括CoreCoder版本、模型名称、API基础URL和使用提示。
    console.print(Panel(
        f"[bold]CoreCoder[/bold] v{__version__}\n"
        f"Model: [cyan]{config.model}[/cyan]"
        + (f"  Base: [dim]{config.base_url}[/dim]" if config.base_url else "")
        + "\nType [bold]/help[/bold] for commands, [bold]Ctrl+C[/bold] to cancel, [bold]quit[/bold] to exit.",
        border_style="blue",
    ))

    # 设置终端输入历史记录文件路径,使用FileHistory类保存用户输入的历史记录,以便在后续会话中可以回溯和重用。
    hist_path = os.path.expanduser("~/.corecoder_history")
    history = FileHistory(hist_path)

    # 设置终端输入快捷键绑定
    @kb.add("enter")  # 当用户按下Enter键时,调用_submit函数提交当前输入缓冲区的内容,并触发验证和处理。
    def _submit(event):
        event.current_buffer.validate_and_handle()

    @kb.add("escape", "enter")  # 当用户按下Esc+Enter组合键时,调用_newline函数在当前输入缓冲区插入一个换行符,以便用户可以输入多行内容。
    def _newline(event):
        event.current_buffer.insert_text("\n")

    while True:
        try:
            # 使用prompt_toolkit库的pt_prompt函数显示提示符并获取用户输入,传入历史记录、快捷键绑定和多行输入选项,并去除首尾空白字符。
            user_input = pt_prompt(
                "You > ",
                history=history,
                multiline=True,
                key_bindings=kb,
                prompt_continuation="...  ",
            ).strip()
        except (EOFError, KeyboardInterrupt):
            # 如果用户按下Ctrl+D或Ctrl+C,则打印退出信息并退出循环,结束交互式会话。
            console.print("\nBye!")
            break
        
        # 如果用户输入为空,则继续等待下一次输入,不进行任何处理。
        if not user_input:
            continue

        # 如果用户输入为"quit"、"exit"、"/quit"或"/exit",则退出循环,结束交互式会话。
        if user_input.lower() in ("quit", "exit", "/quit", "/exit"):
            break

        # 如果用户输入为"/help",则调用_show_help函数显示帮助信息,并继续等待下一次输入。
        if user_input == "/help":
            _show_help()
            continue

        # 如果用户输入为"/reset",则调用智能体的reset方法清除对话历史,并打印会话重置信息。
        if user_input == "/reset":
            agent.reset()
            console.print("[yellow]Conversation reset.[/yellow]")
            continue

        # 如果用户输入为"/tokens",则获取智能体的总提示词令牌数和总完成令牌数,计算总令牌数和估计成本,并打印相关信息。
        if user_input == "/tokens":
            p = agent.llm.total_prompt_tokens
            c = agent.llm.total_completion_tokens
            line = f"Tokens: [cyan]{p}[/cyan] prompt + [cyan]{c}[/cyan] completion = [bold]{p+c}[/bold] total"
            cost = agent.llm.estimated_cost
            if cost is not None:
                line += f"  (~${cost:.4f})"
            console.print(line)
            continue

        # 如果用户输入为"/model"或以"/model "开头,则获取新的模型名称,如果提供了新的模型名称,则切换到该模型并更新配置实例中的模型属性,否则显示当前模型名称。
        if user_input == "/model" or user_input.startswith("/model "):
            new_model = user_input[7:].strip() if user_input.startswith("/model ") else ""
            if new_model:
                agent.llm.model = new_model
                config.model = new_model
                console.print(f"Switched to [cyan]{new_model}[/cyan]")
            else:
                console.print(f"Current model: [cyan]{config.model}[/cyan]")
            continue

        # 如果用户输入为"/compact",则调用智能体的maybe_compress方法压缩对话历史,并打印压缩前后的令牌数和消息数。
        if user_input == "/compact":
            from .context import estimate_tokens
            before = estimate_tokens(agent.messages)
            compressed = agent.context.maybe_compress(agent.messages, agent.llm)
            after = estimate_tokens(agent.messages)
            if compressed:
                console.print(f"[green]Compressed: {before} → {after} tokens ({len(agent.messages)} messages)[/green]")
            else:
                console.print(f"[dim]Nothing to compress ({before} tokens, {len(agent.messages)} messages)[/dim]")
            continue

        # 如果用户输入为"/save",则调用save_session函数保存当前会话到磁盘,并打印保存的会话ID和恢复命令。
        if user_input == "/save":
            sid = save_session(agent.messages, config.model)
            console.print(f"[green]Session saved: {sid}[/green]")
            console.print(f"Resume with: corecoder -r {sid}")
            continue

        # 如果用户输入为"/diff",则导入_changed_files列表,如果该列表为空,则打印没有修改的文件信息,否则打印修改的文件列表。
        if user_input == "/diff":
            from .tools.edit import _changed_files
            if not _changed_files:
                console.print("[dim]No files modified this session.[/dim]")
            else:
                console.print(f"[bold]Files modified this session ({len(_changed_files)}):[/bold]")
                for f in sorted(_changed_files):
                    console.print(f"  [cyan]{f}[/cyan]")
            continue

        # 如果用户输入为"/sessions",则调用list_sessions函数列出已保存的会话,如果没有保存的会话,则打印没有保存的会话信息,否则打印每个会话的ID、模型名称、保存时间和预览内容。
        if user_input == "/sessions":
            sessions = list_sessions()
            if not sessions:
                console.print("[dim]No saved sessions.[/dim]")
            else:
                for s in sessions:
                    console.print(f"  [cyan]{s['id']}[/cyan] ({s['model']}, {s['saved_at']}) {s['preview']}")
            continue

        # 如果用户输入以"/"开头但不是已知命令,则打印未知命令提示信息,并建议使用/help查看帮助。
        if user_input.startswith("/"):
            console.print(f"[yellow]Unknown command: {user_input.split()[0]} (try /help)[/yellow]")
            continue

        # 调用智能体的chat方法处理用户输入,传入on_token和on_tool回调函数,用于处理流式输出和工具调用。
        streamed: list[str] = []

        def on_token(tok):
            """让文字流式输出,每次接收到一个新token时,就打印出来,并刷新终端输出。"""
            streamed.append(tok)
            print(tok, end="", flush=True)

        def on_tool(name, kwargs):
            """当大语言模型调用工具时,打印工具调用信息,包括工具名称和参数的简要表示。"""
            console.print(f"\n[dim]> {name}({_brief(kwargs)})[/dim]")

        try:
            # 调用智能体的chat方法处理用户输入,传入on_token和on_tool回调函数,用于处理流式输出和工具调用。
            response = agent.chat(user_input, on_token=on_token, on_tool=on_tool)

            # 如果流式输出列表streamed不为空,则打印换行符,因为他在on_token回调中已经打印了响应内容
            # 否则使用rich库的Markdown类打印完整的响应内容,以便在终端中显示格式化的文本。
            if streamed:
                print()
            else:
                console.print(Markdown(response))
        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted.[/yellow]")
        except Exception as e:
            console.print(f"\n[red]Error: {e}[/red]")


# 展示帮助
def _show_help():
    console.print(Panel(
        "[bold]Commands:[/bold]\n"
        "  /help          Show this help\n"
        "  /reset         Clear conversation history\n"
        "  /model         Show current model\n"
        "  /model <name>  Switch model mid-conversation\n"
        "  /tokens        Show token usage\n"
        "  /compact       Compress conversation context\n"
        "  /diff          Show files modified this session\n"
        "  /save          Save session to disk\n"
        "  /sessions      List saved sessions\n"
        "  quit           Exit CoreCoder\n"
        "\n"
        "[bold]Input:[/bold]\n"
        "  Enter          Submit message\n"
        "  Esc+Enter      Insert newline (for pasting code)",
        title="CoreCoder Help",
        border_style="dim",
    ))


# 工具调用参数简要表示
def _brief(kwargs: dict, maxlen: int = 80) -> str:
    s = ", ".join(f"{k}={repr(v)[:40]}" for k, v in kwargs.items())
    return s[:maxlen] + ("..." if len(s) > maxlen else "")
