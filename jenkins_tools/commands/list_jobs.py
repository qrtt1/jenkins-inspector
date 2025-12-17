"""List jobs command"""

import sys

from jenkins_tools.core import Command, JenkinsConfig, JenkinsCLI


class ListJobsCommand(Command):
    """List Jenkins jobs in a specific view or all jobs"""

    def __init__(self, args):
        """
        Initialize with command line arguments

        Args:
            args: List of command arguments (sys.argv[2:])
        """
        self.args = args

    def execute(self) -> int:
        """Execute list-jobs command"""
        config = JenkinsConfig()

        # Check if credentials are configured
        if not config.is_configured():
            print("Error: Jenkins credentials not configured.", file=sys.stderr)
            print(f"Run 'jks auth' to configure credentials.", file=sys.stderr)
            return 1

        # Parse arguments
        if not self.args:
            print("Error: Missing argument", file=sys.stderr)
            print("Usage: jks list-jobs <view-name>", file=sys.stderr)
            print("       jks list-jobs --all | -a", file=sys.stderr)
            return 1

        # Check for --all or -a flag
        if self.args[0] in ["--all", "-a"]:
            view_name = None
        else:
            view_name = self.args[0]

        # Execute list-jobs command
        cli = JenkinsCLI(config)

        if view_name:
            # List jobs in specific view
            result = cli.run("list-jobs", view_name)
        else:
            # List all jobs
            result = cli.run("list-jobs")

        if result.returncode == 0:
            output = result.stdout.strip()
            if output:
                print(output)
            else:
                if view_name:
                    print(f"No jobs found in view '{view_name}'")
                else:
                    print("No jobs found")
            return 0
        else:
            if view_name:
                print(f"Error: Failed to list jobs in view '{view_name}'", file=sys.stderr)
            else:
                print("Error: Failed to list jobs", file=sys.stderr)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            return 1
