"Groovy script execution command"

import sys
from pathlib import Path

from jenkins_tools.core import Command, DangerousCommandMixin, JenkinsConfig, JenkinsCLI


class GroovyCommand(DangerousCommandMixin, Command):
    """Execute a Groovy script on the Jenkins server"""

    def __init__(self, args=None):
        """
        Initialize with command line arguments

        Args:
            args: List of command arguments (sys.argv[2:])
                  First argument can be a path to a .groovy file
        """
        self.args = args or []
        super().__init__()

    def execute(self) -> int:
        """Execute groovy command"""
        config = JenkinsConfig()

        # Check if credentials are configured
        if not config.is_configured():
            print("Error: Jenkins credentials not configured.", file=sys.stderr)
            print(f"Run 'jks auth' to configure credentials.", file=sys.stderr)
            return 1

        script_content = ""

        # Case 1: Read from file if provided
        if self.args and not self.args[0].startswith("-"):
            script_path = Path(self.args[0])
            if script_path.exists():
                script_content = script_path.read_text(encoding="utf-8")
            else:
                print(f"Error: Script file not found: {script_path}", file=sys.stderr)
                return 1
        # Case 2: Read from stdin
        elif not sys.stdin.isatty():
            script_content = sys.stdin.read()
        else:
            print("Error: No Groovy script provided.", file=sys.stderr)
            print(
                "Usage: jks groovy <script-file.groovy> [--yes-i-really-mean-it]",
                file=sys.stderr,
            )
            print("   or: echo \"println 'hi'\" | jks groovy", file=sys.stderr)
            return 1

        if not script_content.strip():
            print("Error: Groovy script is empty.", file=sys.stderr)
            return 1

        if self.args and not self.args[0].startswith("-"):
            operation_desc = f"execute groovy script '{self.args[0]}'"
        else:
            operation_desc = "execute groovy script from stdin"

        if not self.require_confirmation(operation_desc):
            return 0

        # Execute groovy command via Jenkins CLI
        # The '=' argument tells Jenkins CLI to read script from stdin
        cli = JenkinsCLI(config)
        result = cli.run("groovy", "=", stdin_input=script_content)

        if result.returncode == 0:
            if result.stdout:
                print(result.stdout, end="")
            return 0
        else:
            print("Error: Failed to execute Groovy script", file=sys.stderr)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            return 1
