"""Update job command"""

import sys

from jenkins_tools.core import Command, JenkinsConfig, JenkinsCLI


class UpdateJobCommand(Command):
    """Update an existing Jenkins job configuration from XML"""

    def __init__(self, args):
        """
        Initialize with command line arguments

        Args:
            args: List of command arguments (sys.argv[2:])
                  First argument is job name
        """
        self.args = args

    def execute(self) -> int:
        """Execute update-job command"""
        config = JenkinsConfig()

        # Check if credentials are configured
        if not config.is_configured():
            print("Error: Jenkins credentials not configured.", file=sys.stderr)
            print(f"Run 'jks auth' to configure credentials.", file=sys.stderr)
            return 1

        # Parse arguments
        if len(self.args) != 1:
            print("Error: Job name is required.", file=sys.stderr)
            print("Usage: jks update-job <job-name> < config.xml", file=sys.stderr)
            return 1

        job_name = self.args[0]

        # Read XML from stdin
        if sys.stdin.isatty():
            print("Error: No XML input provided.", file=sys.stderr)
            print("Usage: jks update-job <job-name> < config.xml", file=sys.stderr)
            print("   or: jks get-job <job> | jks update-job <job>", file=sys.stderr)
            return 1

        xml_content = sys.stdin.read()

        if not xml_content.strip():
            print("Error: XML input is empty.", file=sys.stderr)
            return 1

        # Use Jenkins CLI to update job
        cli = JenkinsCLI(config)
        result = cli.run("update-job", job_name, stdin_input=xml_content)

        if result.returncode != 0:
            print(f"Error: Failed to update job '{job_name}'", file=sys.stderr)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            return 1

        # Success
        print(f"✓ Successfully updated job '{job_name}'")

        return 0
