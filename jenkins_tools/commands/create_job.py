"""Create job command"""

import sys

from jenkins_tools.core import Command, JenkinsConfig, JenkinsCLI


class CreateJobCommand(Command):
    """Create a new Jenkins job from XML configuration"""

    def __init__(self, args=None):
        """
        Initialize with command line arguments

        Args:
            args: List of command arguments (sys.argv[2:])
                  First argument is the new job name
        """
        self.args = args or []

    def execute(self) -> int:
        """Execute create-job command"""
        config = JenkinsConfig()

        # Check if credentials are configured
        if not config.is_configured():
            print("Error: Jenkins credentials not configured.", file=sys.stderr)
            print(f"Run 'jenkee auth' to configure credentials.", file=sys.stderr)
            return 1

        # Parse arguments
        if not self.args:
            print("Error: Missing job name", file=sys.stderr)
            print("Usage: jenkee create-job <job-name> < config.xml", file=sys.stderr)
            print("   or: jenkee get-job existing-job | jenkee create-job new-job", file=sys.stderr)
            return 1

        job_name = self.args[0]

        # Check if stdin has data
        if sys.stdin.isatty():
            print("Error: No XML configuration provided via stdin", file=sys.stderr)
            print("Usage: jenkee create-job <job-name> < config.xml", file=sys.stderr)
            print("   or: jenkee get-job existing-job | jenkee create-job new-job", file=sys.stderr)
            return 1

        # Read XML from stdin
        xml_config = sys.stdin.read()

        if not xml_config.strip():
            print("Error: XML configuration is empty", file=sys.stderr)
            return 1

        # Execute create-job command
        cli = JenkinsCLI(config)
        result = cli.run("create-job", job_name, stdin_input=xml_config)

        if result.returncode == 0:
            # Success
            print(f"✓ Successfully created job '{job_name}'")
            return 0
        else:
            # Failure
            print(f"Error: Failed to create job '{job_name}'", file=sys.stderr)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            return 1
