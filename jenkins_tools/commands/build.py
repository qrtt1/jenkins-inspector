"""Build command"""

import sys

from jenkins_tools.core import Command, JenkinsConfig, JenkinsCLI


class BuildCommand(Command):
    """Trigger a Jenkins job build"""

    def __init__(self, args=None):
        """
        Initialize with command line arguments

        Args:
            args: List of command arguments (sys.argv[2:])
                  First argument is job name
                  Optional flags: -p key=value (multiple), -s, -f, -v
        """
        self.args = args or []

    def execute(self) -> int:
        """Execute build command"""
        config = JenkinsConfig()

        # Check if credentials are configured
        if not config.is_configured():
            print("Error: Jenkins credentials not configured.", file=sys.stderr)
            print(f"Run 'jenkee auth' to configure credentials.", file=sys.stderr)
            return 1

        # Parse arguments
        if not self.args:
            print("Error: Missing job name", file=sys.stderr)
            print(
                "Usage: jenkee build <job-name> [-p key=value ...] [-s] [-f] [-v]", file=sys.stderr
            )
            print("", file=sys.stderr)
            print("Options:", file=sys.stderr)
            print("  -p key=value  Build parameters (can be used multiple times)", file=sys.stderr)
            print("  -s            Wait until build completion", file=sys.stderr)
            print("  -f            Follow build progress (implies -s)", file=sys.stderr)
            print("  -v            Print console output (use with -s or -f)", file=sys.stderr)
            return 1

        job_name = self.args[0]

        # Parse flags and parameters
        cli_args = []
        i = 1
        while i < len(self.args):
            arg = self.args[i]
            if arg == "-p" and i + 1 < len(self.args):
                # Build parameter
                cli_args.append("-p")
                cli_args.append(self.args[i + 1])
                i += 2
            elif arg in ["-s", "-f", "-v"]:
                # Boolean flags
                cli_args.append(arg)
                i += 1
            else:
                print(f"Error: Unknown option '{arg}'", file=sys.stderr)
                return 1

        # Execute build command
        cli = JenkinsCLI(config)
        result = cli.run("build", job_name, *cli_args)

        if result.returncode == 0:
            # Success
            output = result.stdout.strip() if result.stdout else ""
            if output:
                print(output)
            else:
                print(f"✓ Build triggered for job '{job_name}'")
            return 0
        else:
            # Failure
            print(f"Error: Failed to build job '{job_name}'", file=sys.stderr)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            return 1
