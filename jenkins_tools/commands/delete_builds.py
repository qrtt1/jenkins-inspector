"""Delete builds command"""

import sys

from jenkins_tools.core import Command, DangerousCommandMixin, JenkinsConfig, JenkinsCLI


class DeleteBuildsCommand(DangerousCommandMixin, Command):
    """Delete build records for a Jenkins job"""

    def __init__(self, args=None):
        """
        Initialize with command line arguments

        Args:
            args: List of command arguments (sys.argv[2:])
                  First argument is job name
                  Second argument is build range (single number or "start-end")
        """
        self.args = args or []
        super().__init__()

    def execute(self) -> int:
        """Execute delete-builds command"""
        config = JenkinsConfig()

        # Check if credentials are configured
        if not config.is_configured():
            print("Error: Jenkins credentials not configured.", file=sys.stderr)
            print(f"Run 'jenkee auth' to configure credentials.", file=sys.stderr)
            return 1

        # Parse arguments (args already filtered by DangerousCommandMixin)
        if len(self.args) < 2:
            print("Error: Missing required arguments", file=sys.stderr)
            print(
                "Usage: jenkee delete-builds <job-name> <build-range> [--yes-i-really-mean-it]",
                file=sys.stderr,
            )
            print("", file=sys.stderr)
            print("Build range can be:", file=sys.stderr)
            print("  - Single build number: 123", file=sys.stderr)
            print("  - Build range: 100-150", file=sys.stderr)
            return 1

        job_name = self.args[0]
        build_range = self.args[1]

        operation_desc = f"delete build(s) {build_range} for job '{job_name}'"
        if not self.require_confirmation(operation_desc):
            return 0

        # Execute delete-builds command
        cli = JenkinsCLI(config)
        result = cli.run("delete-builds", job_name, build_range)

        if result.returncode == 0:
            # Success
            output = result.stdout.strip() if result.stdout else ""
            if output:
                print(output)
            else:
                print(f"✓ Successfully deleted build(s) {build_range} for job '{job_name}'")
            return 0
        else:
            # Failure
            print(
                f"Error: Failed to delete build(s) {build_range} for job '{job_name}'",
                file=sys.stderr,
            )
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            return 1
