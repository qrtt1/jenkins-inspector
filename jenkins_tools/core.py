"""Core components for Jenkins CLI tools"""

import os
import subprocess
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
from urllib.request import urlretrieve

from dotenv import load_dotenv


# Constants
JENKINS_CLI_JAR_PATH = Path("/tmp/jenkins-inspector/jenkins-cli.jar")


class Command(ABC):
    """Abstract base class for all commands"""

    @abstractmethod
    def execute(self) -> int:
        """
        Execute the command

        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        pass


class DangerousCommandMixin:
    """Mixin for commands that require user confirmation before execution

    This mixin automatically processes the --yes-i-really-mean-it flag:
    - Removes the flag from self.args
    - Stores the skip confirmation state internally
    - Provides require_confirmation() method that checks the stored state

    Usage:
        class MyCommand(DangerousCommandMixin, Command):
            def __init__(self, args=None):
                self.args = args or []
                super().__init__()  # Important: call after setting self.args

            def execute(self):
                # self.args is already filtered
                if not self.require_confirmation("delete something"):
                    return 0
                # ... proceed with operation
    """

    def __init__(self, *args, **kwargs):
        # Process confirmation flag before calling parent __init__
        self._skip_confirmation = False
        if hasattr(self, 'args') and isinstance(self.args, list):
            self._skip_confirmation = "--yes-i-really-mean-it" in self.args
            self.args = [arg for arg in self.args if arg != "--yes-i-really-mean-it"]

        # Call parent class __init__ if it exists
        super().__init__(*args, **kwargs)

    def require_confirmation(self, operation_description: str) -> bool:
        """
        Check for confirmation or prompt for interactive confirmation

        Args:
            operation_description: Description of the operation (e.g., "delete job 'test-job'")

        Returns:
            True if confirmed (either via flag or user input), False if cancelled
        """
        # Check if confirmation flag was present
        if self._skip_confirmation:
            return True

        # Interactive confirmation
        try:
            response = input(f"Are you sure you want to {operation_description}? (y/N): ")
            if response.lower() in ('y', 'yes'):
                return True
            else:
                print("Operation cancelled.")
                return False
        except (EOFError, KeyboardInterrupt):
            print("\nOperation cancelled.")
            return False


class JenkinsConfig:
    """Manage Jenkins configuration"""

    def __init__(self):
        # Load .env from ~/.jenkins-inspector/ only.
        # If a legacy file exists at ~/.jenkins-studio/.env, we intentionally do NOT load it.
        legacy_env_path = Path.home() / ".jenkins-studio" / ".env"
        env_path = Path.home() / ".jenkins-inspector" / ".env"
        # override=False: 環境變數優先於 .env 檔案（重要：讓測試可以覆蓋設定）
        load_dotenv(env_path, override=False)
        self.jenkins_url = os.getenv("JENKINS_URL")
        self.username = os.getenv("JENKINS_USER_ID")
        self.api_token = os.getenv("JENKINS_API_TOKEN")
        self.env_path = env_path
        self.legacy_env_path = legacy_env_path

    @property
    def jenkins_cli_jar_url(self) -> str:
        """Get Jenkins CLI JAR download URL"""
        return f"{self.jenkins_url}jnlpJars/jenkins-cli.jar"

    def is_configured(self) -> bool:
        """Check if Jenkins credentials are configured"""
        return bool(self.jenkins_url and self.username and self.api_token)

    def get_auth_args(self) -> list[str]:
        """Get authentication arguments for jenkins-cli"""
        if not self.is_configured():
            return []
        return ["-auth", f"{self.username}:{self.api_token}"]


class JenkinsCLI:
    """Wrapper for jenkins-cli.jar"""

    def __init__(self, config: JenkinsConfig):
        self.config = config
        self.jar_path = JENKINS_CLI_JAR_PATH

    def ensure_cli_jar(self) -> None:
        """Download jenkins-cli.jar if it doesn't exist"""
        if self.jar_path.exists():
            return

        # Silent download
        self.jar_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            urlretrieve(self.config.jenkins_cli_jar_url, self.jar_path)
        except Exception as e:
            print(f"Error downloading jenkins-cli.jar: {e}", file=sys.stderr)
            sys.exit(1)

    def run(
        self, command: str, *args: str, stdin_input: Optional[str] = None
    ) -> subprocess.CompletedProcess:
        """
        Run a jenkins-cli command

        Args:
            command: Jenkins CLI command (e.g., 'whoami', 'list-jobs')
            *args: Additional arguments for the command
            stdin_input: Optional input to pass to command's stdin

        Returns:
            CompletedProcess object
        """
        self.ensure_cli_jar()

        cmd = [
            "java",
            "-jar",
            str(self.jar_path),
            "-s",
            self.config.jenkins_url,
        ]

        # Add authentication if configured
        auth_args = self.config.get_auth_args()
        if auth_args:
            cmd.append("-http")
            cmd.extend(auth_args)
        else:
            cmd.append("-webSocket")

        # Add the command and its arguments
        cmd.append(command)
        cmd.extend(args)

        return subprocess.run(cmd, input=stdin_input, capture_output=True, text=True)
