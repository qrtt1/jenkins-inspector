"""Stop builds command"""

import sys

from jenkins_tools.core import Command, JenkinsConfig, JenkinsCLI


class StopBuildsCommand(Command):
    """Stop all running builds for specified job(s)"""

    def __init__(self, args=None):
        """
        Initialize with command line arguments

        Args:
            args: List of command arguments (sys.argv[2:])
                  One or more job names
        """
        self.args = args or []

    def execute(self) -> int:
        """Execute stop-builds command"""
        config = JenkinsConfig()

        # Check if credentials are configured
        if not config.is_configured():
            print("Error: Jenkins credentials not configured.", file=sys.stderr)
            print(f"Run 'jenkee auth' to configure credentials.", file=sys.stderr)
            return 1

        # Parse arguments
        if not self.args:
            print("Error: Missing job name(s)", file=sys.stderr)
            print("Usage: jenkee stop-builds <job-name> [job-name ...]", file=sys.stderr)
            return 1

        job_names = self.args

        # Execute stop-builds command
        cli = JenkinsCLI(config)
        result = cli.run("stop-builds", *job_names)

        if result.returncode == 0:
            # Success
            output = result.stdout.strip() if result.stdout else ""
            if output:
                print(output)

            if len(job_names) == 1:
                print(f"✓ Stopped all running builds for job '{job_names[0]}'")
            else:
                print(f"✓ Stopped all running builds for {len(job_names)} job(s)")
                for job in job_names:
                    print(f"  - {job}")
            return 0
        else:
            # Failure
            if len(job_names) == 1:
                print(f"Error: Failed to stop builds for job '{job_names[0]}'", file=sys.stderr)
            else:
                print(f"Error: Failed to stop builds for job(s)", file=sys.stderr)

            if result.stderr:
                print(result.stderr, file=sys.stderr)
            return 1
