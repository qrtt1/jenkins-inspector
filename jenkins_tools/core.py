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

    def require_confirmation(
        self, operation_description: str, config: "Optional[JenkinsConfig]" = None
    ) -> bool:
        """
        Check for confirmation or prompt for interactive confirmation

        Args:
            operation_description: Description of the operation (e.g., "delete job 'test-job'")
            config: The JenkinsConfig in effect for this command. When it's the
                default profile, JenkinsConfig stays silent about it (to avoid
                changing output for default-profile users elsewhere), so this
                method prints the active site here instead -- unconditionally,
                even when --yes-i-really-mean-it skips the interactive prompt.
                Named profiles already announced themselves when JenkinsConfig
                was constructed, so nothing further is printed here for them.

        Returns:
            True if confirmed (either via flag or user input), False if cancelled
        """
        if config is not None and config.profile_name is None:
            print(f"Active profile: default ({config.jenkins_url})", file=sys.stderr)

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

    @staticmethod
    def default_base_dir() -> Path:
        """Directory holding .env, profiles/, and current_profile"""
        return Path.home() / ".jenkins-inspector"

    def __init__(self, base_dir: Optional[Path] = None):
        # Load .env from ~/.jenkins-inspector/ only.
        # If a legacy file exists at ~/.jenkins-studio/.env, we intentionally do NOT load it.
        self.legacy_env_path = Path.home() / ".jenkins-studio" / ".env"
        self.base_dir = base_dir or self.default_base_dir()
        self.env_path = self.base_dir / ".env"
        self.profiles_dir = self.base_dir / "profiles"
        self.current_profile_path = self.base_dir / "current_profile"

        self.profile_name, self.profile_source, error = self._resolve_active_profile()

        if error:
            print(f"Error: {error}", file=sys.stderr)
            sys.exit(1)

        resolved_env_path = (
            self.profiles_dir / f"{self.profile_name}.env"
            if self.profile_name
            else self.env_path
        )

        # 預設 override=False 讓環境變數優先，方便測試不寫檔就能覆蓋設定；
        # 但 named profile 是使用者明確選定的，不該被殘留的 shell export 蓋掉。
        load_dotenv(resolved_env_path, override=self.profile_name is not None)
        self.jenkins_url = os.getenv("JENKINS_URL")
        self.username = os.getenv("JENKINS_USER_ID")
        self.api_token = os.getenv("JENKINS_API_TOKEN")

        if self.profile_name:
            print(f"Active profile: {self.profile_name} ({self.jenkins_url})", file=sys.stderr)

    def _resolve_active_profile(self) -> tuple[Optional[str], str, Optional[str]]:
        """
        Determine which profile should be loaded.

        Returns:
            (profile_name, source, error_message). profile_name is None when the
            default ~/.jenkins-inspector/.env should be used. error_message is set
            when a named profile was requested but its file is missing -- callers
            must treat that as fatal, never fall back silently to the default.
        """
        env_profile = os.getenv("JENKEE_PROFILE", "").strip()
        if env_profile:
            profile_path = self.profiles_dir / f"{env_profile}.env"
            if not profile_path.exists():
                return None, "env-override", (
                    f"profile '{env_profile}' not found at {profile_path}.\n"
                    f"Run 'jenkee profile list' to see available profiles, "
                    f"or unset JENKEE_PROFILE to use the default config."
                )
            return env_profile, "env-override", None

        if self.current_profile_path.exists():
            try:
                state_profile = self.current_profile_path.read_text().strip()
            except (OSError, UnicodeDecodeError) as exc:
                return None, "persistent", (
                    f"current_profile at {self.current_profile_path} is unreadable ({exc}).\n"
                    f"Run 'jenkee profile use --default' or 'jenkee profile use <name>' to fix this."
                )
            if state_profile:
                profile_path = self.profiles_dir / f"{state_profile}.env"
                if not profile_path.exists():
                    return None, "persistent", (
                        f"current profile '{state_profile}' (set via 'jenkee profile use') "
                        f"no longer exists at {profile_path}.\n"
                        f"Run 'jenkee profile use --default' or 'jenkee profile use <name>' to fix this."
                    )
                return state_profile, "persistent", None

        return None, "default", None

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
