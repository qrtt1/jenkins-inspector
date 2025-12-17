"""Copy job command"""

import sys

from jenkins_tools.core import Command, JenkinsConfig, JenkinsCLI


class CopyJobCommand(Command):
    """Copy an existing Jenkins job to a new job"""

    def __init__(self, args):
        """
        Initialize with command line arguments

        Args:
            args: List of command arguments (sys.argv[2:])
                  First argument is source job name, second is destination job name
        """
        self.args = args

    def execute(self) -> int:
        """Execute copy-job command"""
        config = JenkinsConfig()

        # Check if credentials are configured
        if not config.is_configured():
            print("Error: Jenkins credentials not configured.", file=sys.stderr)
            print(f"Run 'jks auth' to configure credentials.", file=sys.stderr)
            return 1

        # Parse arguments
        if len(self.args) != 2:
            print("Error: Source and destination job names are required.", file=sys.stderr)
            print("Usage: jks copy-job <source-job> <destination-job>", file=sys.stderr)
            return 1

        source_job = self.args[0]
        dest_job = self.args[1]

        # Use Jenkins CLI to copy job
        cli = JenkinsCLI(config)
        result = cli.run("copy-job", source_job, dest_job)

        if result.returncode != 0:
            print(f"Error: Failed to copy job '{source_job}' to '{dest_job}'", file=sys.stderr)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            return 1

        # Success
        print(f"✓ Successfully copied job '{source_job}' to '{dest_job}'")

        return 0
