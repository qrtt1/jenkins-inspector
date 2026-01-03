"""dev-qa command - hidden command for testing purposes"""

import sys
from pathlib import Path

from jenkins_tools.core import Command


class DevQACommand(Command):
    """Hidden dev-qa command to toggle config directory for testing"""

    def __init__(self, args: list[str]):
        self.args = args
        self.config_dir = Path.home() / ".jenkins-inspector"
        self.disabled_config_dir = Path.home() / ".jenkins-inspector-disable-by-qa"

    def execute(self) -> int:
        """Execute dev-qa command"""
        if not self.args:
            print("Error: Missing argument", file=sys.stderr)
            print("Usage: jenkee dev-qa --enable|--disable", file=sys.stderr)
            return 1

        action = self.args[0]

        if action == "--enable":
            return self._enable_qa_mode()
        elif action == "--disable":
            return self._disable_qa_mode()
        else:
            print(f"Error: Unknown option '{action}'", file=sys.stderr)
            print("Usage: jenkee dev-qa --enable|--disable", file=sys.stderr)
            return 1

    def _enable_qa_mode(self) -> int:
        """Enable QA mode by hiding production config"""
        if self.disabled_config_dir.exists():
            print(
                f"Error: Backup config already exists at: {self.disabled_config_dir}",
                file=sys.stderr,
            )
            print("QA mode is already enabled or previous backup was not restored.", file=sys.stderr)
            return 1

        if not self.config_dir.exists():
            print(
                f"Info: No config directory found at: {self.config_dir}",
                file=sys.stderr,
            )
            print("QA mode enabled (nothing to disable).", file=sys.stderr)
            return 0

        try:
            self.config_dir.rename(self.disabled_config_dir)
            print(f"✓ QA mode enabled")
            print(f"  Renamed: {self.config_dir}")
            print(f"  To: {self.disabled_config_dir}")
            return 0
        except Exception as e:
            print(f"Error: Failed to rename config directory: {e}", file=sys.stderr)
            return 1

    def _disable_qa_mode(self) -> int:
        """Disable QA mode by restoring production config"""
        if not self.disabled_config_dir.exists():
            print(
                f"Error: No backup config found at: {self.disabled_config_dir}",
                file=sys.stderr,
            )
            print("QA mode is not enabled or backup was already restored.", file=sys.stderr)
            return 1

        if self.config_dir.exists():
            print(
                f"Error: Config directory already exists at: {self.config_dir}",
                file=sys.stderr,
            )
            print("Please manually resolve the conflict.", file=sys.stderr)
            return 1

        try:
            self.disabled_config_dir.rename(self.config_dir)
            print(f"✓ QA mode disabled")
            print(f"  Restored: {self.disabled_config_dir}")
            print(f"  To: {self.config_dir}")
            return 0
        except Exception as e:
            print(f"Error: Failed to restore config directory: {e}", file=sys.stderr)
            return 1
