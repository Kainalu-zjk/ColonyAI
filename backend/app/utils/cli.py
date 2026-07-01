"""Enhanced CLI module — interactive and headless modes for Colony AI.

Supports:
  python -m app.main cli --mode interactive|single
  python -m app.main cli --file problem.txt --template china|american --output markdown|latex
  python -m app.main serve
"""

import argparse
import asyncio
import os
import sys
from textwrap import dedent

from app.utils.log_util import logger
from app.core.workflow import MathModelWorkFlow
from app.schemas.enums import CompTemplate, FormatOutPut
from app.schemas.request import Problem
from app.utils.common_utils import create_task_id, create_work_dir


def center_cli_str(text: str, width: int | None = None):
    """Center multi-line text in the terminal."""
    import shutil
    width = width or shutil.get_terminal_size().columns
    lines = text.split("\n")
    max_line_len = max(len(line) for line in lines)
    return "\n".join(
        (line + " " * (max_line_len - len(line))).center(width) for line in lines
    )


def get_ascii_banner(center: bool = True) -> str:
    text = dedent(r"""
    ===============================================================================
      ___    __            _
     / __|  / _|  ___     | |_   ___   _ _   ___
    | (__  |  _| / -_)    |  _| / _ \ | '_| / -_)
     \___| |_|   \___|     \__| \___/ |_|   \___|
      ___    _   _         ____    ___
     / __|  | | (_)       |_  /   / _ \
    | (__   | | | |  ___   / /   | (_) |
     \___|  |_| |_| |___| /___|   \__\_\
                 |__/
    ===============================================================================
    """).strip()
    if center:
        return center_cli_str(text)
    return text


def _print_info():
    print(get_ascii_banner())
    print(center_cli_str("Colony AI v0.3.0"))
    print(center_cli_str("GitHub: https://github.com/jihe520/MathModelAgent"))
    print()


async def _run_cli_single(ques_all: str, comp_template: str, format_output: str,
                          lang: str = "zh", files: list[str] | None = None):
    """Run a single task headlessly."""
    task_id = create_task_id()
    work_dir = create_work_dir(task_id)

    # Copy files to work dir if provided
    if files:
        for file_path in files:
            if os.path.exists(file_path):
                import shutil
                dst = os.path.join(work_dir, os.path.basename(file_path))
                shutil.copy2(file_path, dst)
                print(f"  Copied: {file_path} -> {dst}")

    template = CompTemplate.AMERICAN if comp_template == "american" else CompTemplate.CHINA
    output = FormatOutPut.LaTeX if format_output == "latex" else FormatOutPut.Markdown

    problem = Problem(
        task_id=task_id,
        ques_all=ques_all,
        comp_template=template,
        format_output=output,
    )

    print(f"\n  Task ID: {task_id}")
    print(f"  Template: {comp_template}")
    print(f"  Output: {format_output}")
    print(f"  Language: {lang}")
    print()

    workflow = MathModelWorkFlow()
    try:
        await workflow.execute(problem)
        print(f"\n  ✓ Task completed. Results in: {work_dir}")
        res_file = os.path.join(work_dir, "res.md")
        if os.path.exists(res_file):
            print(f"  ✓ Paper saved to: {res_file}")
    except asyncio.CancelledError:
        print("\n  ✗ Task was cancelled.")
    except Exception as e:
        print(f"\n  ✗ Task failed: {e}")

    return task_id


async def _run_cli_interactive():
    """Run the CLI in interactive mode — step by step."""
    print("\n  === Interactive Mode ===")
    print()

    # Step 1: Problem text
    print("  Step 1: Enter the problem description.")
    print("  (Type your problem. End with Ctrl+Z on Windows or Ctrl+D on Unix)")
    print()
    lines = []
    try:
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        pass
    ques_all = "\n".join(lines).strip()
    if not ques_all:
        print("  No input provided. Aborting.")
        return

    # Step 2: Competition template
    print()
    template_input = input("  Competition template (china/american) [china]: ").strip().lower()
    comp_template = "american" if template_input.startswith("a") else "china"

    # Step 3: Output format
    fmt_input = input("  Output format (markdown/latex) [markdown]: ").strip().lower()
    format_output = "latex" if fmt_input.startswith("l") else "markdown"

    # Step 4: Language
    lang_input = input("  Language (zh/en) [zh]: ").strip().lower()
    lang = "en" if lang_input.startswith("e") else "zh"

    # Step 5: Data files (optional)
    files_input = input("  Data file paths (comma-separated, or empty): ").strip()
    files = [f.strip() for f in files_input.split(",") if f.strip()] if files_input else None

    print()
    print("  Starting task with:")
    print(f"    Template: {comp_template}")
    print(f"    Format: {format_output}")
    print(f"    Language: {lang}")
    if files:
        print(f"    Files: {files}")
    print()

    await _run_cli_single(ques_all, comp_template, format_output, lang, files)


def _interactive_input(prompt: str, default: str = "") -> str:
    """Get interactive input from user."""
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        return default


def build_cli_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Colony AI (智衍) — Multi-Agent Collaboration Platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=dedent("""
            Examples:
              python -m app.main serve                        # Start web server
              python -m app.main cli --file problem.txt       # Run from file
              python -m app.main cli --mode interactive       # Interactive mode
              python -m app.main cli --list-models            # List templates
        """),
    )
    parser.add_argument("command", nargs="?", default="serve",
                        choices=["serve", "cli"],
                        help="Command: 'serve' (default) starts the web server, 'cli' runs CLI mode")
    parser.add_argument("--mode", choices=["interactive", "single"], default="single",
                        help="CLI mode: interactive (step-by-step) or single (from file)")
    parser.add_argument("-f", "--file", type=str, default="",
                        help="Path to problem description file (for single mode)")
    parser.add_argument("-t", "--template", choices=["china", "american"], default="china",
                        help="Competition template")
    parser.add_argument("-o", "--output", choices=["markdown", "latex"], default="markdown",
                        help="Output format")
    parser.add_argument("-l", "--lang", choices=["zh", "en"], default="zh",
                        help="Output language")
    parser.add_argument("-d", "--data", type=str, default="",
                        help="Comma-separated list of data files to include")
    parser.add_argument("--list-models", action="store_true",
                        help="List available competition templates and exit")
    parser.add_argument("--host", type=str, default="0.0.0.0",
                        help="Server host (for 'serve' command)")
    parser.add_argument("-p", "--port", type=int, default=8000,
                        help="Server port (for 'serve' command)")
    parser.add_argument("--reload", action="store_true",
                        help="Enable auto-reload (for 'serve' command)")
    return parser


async def cli_main(argv: list[str] | None = None):
    """CLI entry point."""
    parser = build_cli_parser()
    args = parser.parse_args(argv)

    print(get_ascii_banner())
    print(center_cli_str("GitHub: https://github.com/jihe520/MathModelAgent"))

    # Handle --list-models
    if args.list_models:
        print("  Available templates:")
        print("    - china   (中文竞赛模板 — 国赛/华数杯/华为杯等)")
        print("    - american (MCM/ICM English template)")
        print()
        print("  Available output formats:")
        print("    - markdown (.md)")
        print("    - latex    (.tex, via template)")
        print()
        return

    if args.command == "cli":
        if args.mode == "interactive":
            await _run_cli_interactive()
        else:
            # Single file mode
            if args.file:
                file_path = args.file
                if not os.path.exists(file_path):
                    print(f"  Error: File '{file_path}' not found.")
                    sys.exit(1)
                with open(file_path, "r", encoding="utf-8") as f:
                    ques_all = f.read()
                data_files = [f.strip() for f in args.data.split(",") if f.strip()] if args.data else None
                await _run_cli_single(ques_all, args.template, args.output, args.lang, data_files)
            else:
                print("  Error: --file is required in 'single' mode.")
                print("  Use --mode interactive for step-by-step input.")
                sys.exit(1)
    else:
        # 'serve' command — start web server (handled by run_uvicorn in main.py entry)
        from app.main import app
        import uvicorn
        uvicorn.run(
            "app.main:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
        )


if __name__ == "__main__":
    asyncio.run(cli_main())
