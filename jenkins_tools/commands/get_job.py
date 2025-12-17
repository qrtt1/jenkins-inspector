"""Get job command"""

import sys

from jenkins_tools.core import Command, JenkinsConfig, JenkinsCLI


class GetJobCommand(Command):
    """Get Jenkins job XML configuration"""

    def __init__(self, args):
        """
        Initialize with command line arguments

        Args:
            args: List of command arguments (sys.argv[2:])
        """
        self.args = args

    def execute(self) -> int:
        """Execute get-job-config command"""
        config = JenkinsConfig()

        # Check if credentials are configured
        if not config.is_configured():
            print("Error: Jenkins credentials not configured.", file=sys.stderr)
            print(f"Run 'jks auth' to configure credentials.", file=sys.stderr)
            return 1

        # Parse arguments
        if not self.args:
            print("Error: Missing job name", file=sys.stderr)
            print("Usage: jks get-job <job-name>", file=sys.stderr)
            return 1

        job_name = self.args[0]

        # Execute get-job command
        cli = JenkinsCLI(config)
        result = cli.run("get-job", job_name)

        if result.returncode == 0:
            print(result.stdout)
            return 0
        else:
            print(f"Error: Failed to get config for job '{job_name}'", file=sys.stderr)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            return 1
