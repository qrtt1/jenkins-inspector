"""Help command"""

import sys
from pathlib import Path

from jenkins_tools import __version__
from jenkins_tools.core import Command


class HelpCommand(Command):
    """Display help information for commands"""

    # 命令說明對照表
    COMMAND_DESCRIPTIONS = {
        "auth": "Verify Jenkins authentication",
        "list-views": "List all Jenkins views",
        "list-jobs": "List jobs in a view or all jobs",
        "get-job": "Get job XML configuration",
        "list-builds": "List build history for a job",
        "console": "Get console output of a build",
        "job-status": "Show job status and triggers",
        "job-diff": "Compare two job configurations",
        "list-credentials": "List Jenkins credentials metadata",
        "describe-credentials": "Describe a specific credential",
        "add-job-to-view": "Add jobs to a view",
        "copy-job": "Copy a job to a new job",
        "update-job": "Update job configuration from XML",
        "build": "Trigger a Jenkins job build",
        "stop-builds": "Stop all running builds for job(s)",
        "create-job": "Create a new job from XML configuration",
        "delete-job": "Delete one or more jobs (IRREVERSIBLE)",
        "disable-job": "Disable one or more jobs",
        "enable-job": "Enable one or more jobs",
        "delete-builds": "Delete build records (IRREVERSIBLE)",
        "groovy": "Execute a Groovy script on the server",
        "domain": "Manage credentials domains",
        "prompt": "Display AI agent guide for using jenkee",
        "help": "Show help information",
        "dev-qa": "Toggle config directory for jenkee QA testing (internal use)",
    }

    # 危險命令集合（需要使用者確認才能執行）
    DANGEROUS_COMMANDS = {
        "delete-job",  # 刪除 job（不可逆）
        "disable-job",  # 停用 job
        "enable-job",  # 啟用 job
        "delete-builds",  # 刪除 build 記錄（不可逆）
        "groovy",  # 可執行任意操作
    }

    # 隱藏命令集合（不在一般 help 中顯示）
    HIDDEN_COMMANDS = {
        "dev-qa",  # 測試用命令
    }

    def __init__(self, args=None):
        """
        Initialize with command line arguments

        Args:
            args: List of command arguments (sys.argv[2:])
                  If empty, show command list
                  If contains command name, show detailed help for that command
                  Can include --all flag to show dangerous commands
        """
        self.args = args or []
        self.show_dangerous = "--all" in self.args
        # 移除 flag，只保留命令名稱
        self.args = [arg for arg in self.args if arg != "--all"]

    def execute(self) -> int:
        """Execute help command"""
        # 沒有參數：顯示所有命令列表
        if not self.args:
            self._show_command_list()
            return 0

        # 有參數：顯示特定命令的詳細說明
        command = self.args[0]
        return self._show_command_help(command)

    def _show_command_list(self):
        """顯示所有可用命令的列表"""
        program_name = Path(sys.argv[0]).name if sys.argv else "jenkee"
        print(f"Jenkins Inspector CLI v{__version__}")
        print()
        print(f"Usage: {program_name} <command> [options]")
        print(f"       {program_name} help <command>  Show detailed help for a command")
        print()

        # 根據是否顯示危險命令，分類顯示
        safe_commands = []
        dangerous_commands = []
        hidden_commands = []

        for cmd in sorted(self.COMMAND_DESCRIPTIONS.keys()):
            if cmd in self.HIDDEN_COMMANDS:
                hidden_commands.append(cmd)
            elif cmd in self.DANGEROUS_COMMANDS:
                dangerous_commands.append(cmd)
            else:
                safe_commands.append(cmd)

        # 顯示一般命令
        print("Available commands:")
        print()
        for cmd in safe_commands:
            desc = self.COMMAND_DESCRIPTIONS[cmd]
            print(f"  {cmd:25s} {desc}")

        # 如果有 --all flag，顯示危險命令
        if self.show_dangerous and dangerous_commands:
            print()
            print("Dangerous commands (require user confirmation):")
            print()
            for cmd in dangerous_commands:
                desc = self.COMMAND_DESCRIPTIONS[cmd]
                print(f"  {cmd:25s} {desc} ⚠️")

        # 如果有 --all flag，顯示隱藏命令
        if self.show_dangerous and hidden_commands:
            print()
            print("Hidden commands (for internal use):")
            print()
            for cmd in hidden_commands:
                desc = self.COMMAND_DESCRIPTIONS[cmd]
                print(f"  {cmd:25s} {desc}")

        print()
        print(
            f"Run '{program_name} help <command>' for detailed information about a specific command."
        )

    def _show_command_help(self, command: str) -> int:
        """
        顯示特定命令的詳細說明

        Args:
            command: 命令名稱

        Returns:
            0 if successful, 1 if command not found or doc file missing
        """
        # 檢查命令是否存在
        if command not in self.COMMAND_DESCRIPTIONS:
            print(f"Error: Unknown command '{command}'", file=sys.stderr)
            program_name = Path(sys.argv[0]).name if sys.argv else "jenkee"
            print(f"Run '{program_name} help' to see available commands.", file=sys.stderr)
            return 1

        # 嘗試讀取文件檔案
        doc_content = self._load_doc_file(command)
        if doc_content is None:
            print(f"Error: No documentation found for command '{command}'", file=sys.stderr)
            print(f"See online documentation: https://github.com/qrtt1/jenkins-inspector/blob/main/docs/examples/{command}.md", file=sys.stderr)
            return 1

        # 顯示文件內容，並動態替換相對路徑為 GitHub URLs
        doc_content = self._replace_relative_links(doc_content)
        print(doc_content)
        return 0

    def _replace_relative_links(self, content: str) -> str:
        """
        將文件中的相對路徑替換為 GitHub URLs

        Args:
            content: 文件內容

        Returns:
            替換後的文件內容
        """
        import re

        base_url = "https://github.com/qrtt1/jenkins-inspector/blob/main"

        # 替換模式：[text](relative/path.md)
        # 匹配相對路徑（包含 ../ 或直接的檔案名）
        def replace_link(match):
            link_text = match.group(1)
            link_path = match.group(2)

            # 只處理 .md 檔案的相對路徑
            if not link_path.startswith('http') and link_path.endswith('.md'):
                # 處理 ../../README.md 這種形式
                if link_path.startswith('../../'):
                    # docs/examples/../../README.md -> README.md
                    new_path = link_path.replace('../../', '')
                    return f"[{link_text}]({base_url}/{new_path})"
                # 處理 ../examples/ 這種形式
                elif link_path.startswith('../'):
                    # docs/examples/../examples/ -> docs/examples/
                    new_path = link_path.replace('../', 'docs/')
                    return f"[{link_text}]({base_url}/{new_path})"
                # 處理同層檔案 list-credentials.md
                elif '/' not in link_path:
                    return f"[{link_text}]({base_url}/docs/examples/{link_path})"

            # 不符合條件的保持原樣
            return match.group(0)

        # 使用正則表達式替換
        pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        return re.sub(pattern, replace_link, content)

    def _load_doc_file(self, command: str):
        """
        載入命令的文件檔案

        Args:
            command: 命令名稱

        Returns:
            文件內容，如果檔案不存在則返回 None
        """
        # 嘗試多種路徑來找到文件
        # 1. 從安裝的 package 中讀取 (使用 importlib.resources)
        try:
            import importlib.resources as resources

            try:
                # Python 3.9+
                doc_file = resources.files("jenkins_tools").joinpath(f"docs/examples/{command}.md")
                if doc_file.is_file():
                    return doc_file.read_text(encoding="utf-8")
            except AttributeError:
                # Python 3.8
                with resources.path("jenkins_tools", "docs") as docs_path:
                    doc_file = docs_path / "examples" / f"{command}.md"
                    if doc_file.exists():
                        return doc_file.read_text(encoding="utf-8")
        except (FileNotFoundError, ModuleNotFoundError):
            pass

        # 2. 從開發環境讀取（相對於此檔案的位置）
        current_file = Path(__file__)
        # jenkins_tools/commands/help.py -> jenkins_tools/ -> root/
        project_root = current_file.parent.parent.parent
        doc_file = project_root / "docs" / "examples" / f"{command}.md"

        if doc_file.exists():
            return doc_file.read_text(encoding="utf-8")

        return None
