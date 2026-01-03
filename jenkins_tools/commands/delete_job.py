"""Delete job command"""

import sys

from jenkins_tools.core import Command, DangerousCommandMixin, JenkinsConfig, JenkinsCLI


class DeleteJobCommand(DangerousCommandMixin, Command):
    """Delete one or more Jenkins jobs"""

    def __init__(self, args=None):
        """
        Initialize with command line arguments

        Args:
            args: List of command arguments (sys.argv[2:])
                  One or more job names to delete
        """
        self.args = args or []
        super().__init__()

    def execute(self) -> int:
        """Execute delete-job command"""
        config = JenkinsConfig()

        # Check if credentials are configured
        if not config.is_configured():
            print("Error: Jenkins credentials not configured.", file=sys.stderr)
            print(f"Run 'jenkee auth' to configure credentials.", file=sys.stderr)
            return 1

        # Parse arguments (args already filtered by DangerousCommandMixin)
        if not self.args:
            print("Error: Missing job name(s)", file=sys.stderr)
            print("Usage: jenkee delete-job <job-name> [job-name ...] [--yes-i-really-mean-it]", file=sys.stderr)
            return 1

        job_names = self.args

        # Prepare operation description for confirmation
        if len(job_names) == 1:
            operation_desc = f"delete job '{job_names[0]}'"
        else:
            operation_desc = f"delete {len(job_names)} job(s)"

        # Require confirmation
        if not self.require_confirmation(operation_desc):
            return 0

        # Delete each job
        cli = JenkinsCLI(config)
        failed_jobs = []

        for job_name in job_names:
            result = cli.run("delete-job", job_name)

            if result.returncode != 0:
                failed_jobs.append(job_name)
                print(f"Error: Failed to delete job '{job_name}'", file=sys.stderr)
                if result.stderr:
                    print(result.stderr, file=sys.stderr)

        # Print success message
        if len(failed_jobs) == 0:
            if len(job_names) == 1:
                print(f"✓ Successfully deleted job '{job_names[0]}'")
            else:
                print(f"✓ Successfully deleted {len(job_names)} job(s)")
                for job_name in job_names:
                    print(f"  - {job_name}")
            return 0
        else:
            # Some jobs failed
            if len(failed_jobs) < len(job_names):
                # Partial success
                success_count = len(job_names) - len(failed_jobs)
                print(
                    f"Warning: {success_count} job(s) deleted, {len(failed_jobs)} failed",
                    file=sys.stderr,
                )
            return 1
