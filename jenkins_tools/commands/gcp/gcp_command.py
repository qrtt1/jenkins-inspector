"""GCP command dispatcher"""

import sys
from pathlib import Path

from jenkins_tools.core import Command
from jenkins_tools.commands.gcp.credential import CredentialCommand


class GCPCommand(Command):
    """
    GCP subcommand dispatcher

    Handles: jenkee gcp <resource> <action> [args...]
    Currently supports: credential
    """

    def __init__(self, args):
        """
        Initialize with command line arguments

        Args:
            args: List of command arguments (sys.argv[2:])
                  First arg should be resource type (e.g., 'credential')
                  Remaining args are passed to the resource handler
        """
        self.args = args

    def execute(self) -> int:
        """Execute GCP subcommand"""
        if len(self.args) == 0 or self.args[0] in ("--help", "-h"):
            self._show_help()
            return 0

        resource = self.args[0]
        resource_args = self.args[1:]

        # Dispatch to appropriate resource handler
        if resource == "credential":
            cmd = CredentialCommand(resource_args)
            return cmd.execute()
        else:
            program_name = Path(sys.argv[0]).name if sys.argv else "jenkee"
            print(f"Error: Unknown GCP resource '{resource}'", file=sys.stderr)
            print(f"Run '{program_name} gcp --help' to see available resources", file=sys.stderr)
            return 1

    def _show_help(self):
        """Show GCP subcommand help"""
        program_name = Path(sys.argv[0]).name if sys.argv else "jenkee"
        print(f"Usage: {program_name} gcp <resource> <action> [options]")
        print()
        print("GCP resources:")
        print()
        print("  credential              Manage GCP Service Account credentials")
        print()
        print("Examples:")
        print(f"  {program_name} gcp credential create <id> <json-key-file>")
        print(f"  {program_name} gcp credential list")
        print(f"  {program_name} gcp credential describe <id>")
        print(f"  {program_name} gcp credential update <id> <json-key-file>")
        print(f"  {program_name} gcp credential delete <id>")
        print()
        print(f"Run '{program_name} gcp credential --help' for detailed credential management help")
