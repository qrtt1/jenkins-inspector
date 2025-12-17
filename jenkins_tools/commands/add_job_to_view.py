"""Add jobs to view command"""

import sys

from jenkins_tools.core import Command, JenkinsConfig, JenkinsCLI


class AddJobToViewCommand(Command):
    """Add one or more jobs to a Jenkins view"""

    def __init__(self, args):
        """
        Initialize with command line arguments

        Args:
            args: List of command arguments (sys.argv[2:])
                  First argument is view name, rest are job names
        """
        self.args = args

    def execute(self) -> int:
        """Execute add-job-to-view command"""
        config = JenkinsConfig()

        # Check if credentials are configured
        if not config.is_configured():
            print("Error: Jenkins credentials not configured.", file=sys.stderr)
            print(f"Run 'jks auth' to configure credentials.", file=sys.stderr)
            return 1

        # Parse arguments
        if len(self.args) < 2:
            print("Error: View name and at least one job name are required.", file=sys.stderr)
            print(
                "Usage: jks add-job-to-view <view-name> <job-name> [job-name ...]", file=sys.stderr
            )
            return 1

        view_name = self.args[0]
        job_names = self.args[1:]

        # Use Jenkins CLI to add jobs to view
        cli = JenkinsCLI(config)
        result = cli.run("add-job-to-view", view_name, *job_names)

        if result.returncode != 0:
            print(f"Error: Failed to add jobs to view '{view_name}'", file=sys.stderr)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            return 1

        # Success
        print(f"✓ Successfully added {len(job_names)} job(s) to view '{view_name}'")
        for job in job_names:
            print(f"  - {job}")

        return 0
