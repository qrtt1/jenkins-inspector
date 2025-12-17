"""Job diff command"""

import sys
import difflib

from jenkins_tools.core import Command, JenkinsConfig, JenkinsCLI


class JobDiffCommand(Command):
    """Compare configuration of two Jenkins jobs"""

    def __init__(self, args):
        """
        Initialize with command line arguments

        Args:
            args: List of command arguments (sys.argv[2:])
        """
        self.args = args

    def execute(self) -> int:
        """Execute job-diff command"""
        config = JenkinsConfig()

        # Check if credentials are configured
        if not config.is_configured():
            print("Error: Jenkins credentials not configured.", file=sys.stderr)
            print(f"Run 'jks auth' to configure credentials.", file=sys.stderr)
            return 1

        # Parse arguments
        if len(self.args) < 2:
            print("Error: Missing job names", file=sys.stderr)
            print("Usage: jks job-diff <job-name-1> <job-name-2>", file=sys.stderr)
            return 1

        job1_name = self.args[0]
        job2_name = self.args[1]

        # Get both job configurations
        cli = JenkinsCLI(config)

        result1 = cli.run("get-job", job1_name)
        if result1.returncode != 0:
            print(f"Error: Failed to get job '{job1_name}'", file=sys.stderr)
            if result1.stderr:
                print(result1.stderr, file=sys.stderr)
            return 1

        result2 = cli.run("get-job", job2_name)
        if result2.returncode != 0:
            print(f"Error: Failed to get job '{job2_name}'", file=sys.stderr)
            if result2.stderr:
                print(result2.stderr, file=sys.stderr)
            return 1

        # Split into lines for diff
        lines1 = result1.stdout.splitlines(keepends=True)
        lines2 = result2.stdout.splitlines(keepends=True)

        # Generate unified diff
        diff = difflib.unified_diff(
            lines1, lines2, fromfile=job1_name, tofile=job2_name, lineterm=""
        )

        # Output diff
        diff_lines = list(diff)
        if not diff_lines:
            print(f"No differences found between '{job1_name}' and '{job2_name}'")
            return 0

        for line in diff_lines:
            print(line)

        return 0
