"""Console command"""

import sys

from jenkins_tools.core import Command, JenkinsConfig, JenkinsCLI


class ConsoleCommand(Command):
    """Get console output of a Jenkins build"""

    def __init__(self, args):
        """
        Initialize with command line arguments

        Args:
            args: List of command arguments (sys.argv[2:])
        """
        self.args = args

    def execute(self) -> int:
        """Execute console command"""
        config = JenkinsConfig()

        # Check if credentials are configured
        if not config.is_configured():
            print("Error: Jenkins credentials not configured.", file=sys.stderr)
            print(f"Run 'jks auth' to configure credentials.", file=sys.stderr)
            return 1

        # Parse arguments
        if not self.args:
            print("Error: Missing job name", file=sys.stderr)
            print("Usage: jks console <job-name> [build-number]", file=sys.stderr)
            return 1

        job_name = self.args[0]
        build_number = self.args[1] if len(self.args) > 1 else "lastBuild"

        # Execute console command
        cli = JenkinsCLI(config)
        result = cli.run("console", job_name, build_number)

        if result.returncode == 0:
            print(result.stdout, end="")
            return 0
        else:
            print(
                f"Error: Failed to get console output for job '{job_name}' build {build_number}",
                file=sys.stderr,
            )
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            return 1
