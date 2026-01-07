"""Jenkins CLI main entry point"""

import sys
from pathlib import Path

from jenkins_tools.commands import (
    AuthCommand,
    ListViewsCommand,
    ListJobsCommand,
    GetJobCommand,
    ListBuildsCommand,
    ConsoleCommand,
    JobStatusCommand,
    JobDiffCommand,
    ListCredentialsCommand,
    DescribeCredentialsCommand,
    AddJobToViewCommand,
    CopyJobCommand,
    UpdateJobCommand,
    BuildCommand,
    StopBuildsCommand,
    CreateJobCommand,
    DeleteJobCommand,
    DisableJobCommand,
    EnableJobCommand,
    DeleteBuildsCommand,
    GroovyCommand,
    DomainCommand,
    HelpCommand,
    PromptCommand,
    DevQACommand,
)
from jenkins_tools.commands.gcp import GCPCommand


def main():
    """Main entry point for CLI command"""
    program_name = Path(sys.argv[0]).name if sys.argv else "jenkee"
    if len(sys.argv) < 2:
        # 沒有參數時顯示命令列表
        cmd = HelpCommand()
        sys.exit(cmd.execute())

    command = sys.argv[1]

    # Handle global --help or -h flag
    if command in ("--help", "-h"):
        cmd = HelpCommand(sys.argv[2:])
        sys.exit(cmd.execute())

    # Dispatch to appropriate command
    if command == "auth":
        cmd = AuthCommand()
        sys.exit(cmd.execute())
    elif command == "list-views":
        cmd = ListViewsCommand()
        sys.exit(cmd.execute())
    elif command == "list-jobs":
        cmd = ListJobsCommand(sys.argv[2:])
        sys.exit(cmd.execute())
    elif command == "get-job":
        cmd = GetJobCommand(sys.argv[2:])
        sys.exit(cmd.execute())
    elif command == "list-builds":
        cmd = ListBuildsCommand(sys.argv[2:])
        sys.exit(cmd.execute())
    elif command == "console":
        cmd = ConsoleCommand(sys.argv[2:])
        sys.exit(cmd.execute())
    elif command == "job-status":
        cmd = JobStatusCommand(sys.argv[2:])
        sys.exit(cmd.execute())
    elif command == "job-diff":
        cmd = JobDiffCommand(sys.argv[2:])
        sys.exit(cmd.execute())
    elif command == "list-credentials":
        cmd = ListCredentialsCommand(sys.argv[2:])
        sys.exit(cmd.execute())
    elif command == "describe-credentials":
        cmd = DescribeCredentialsCommand(sys.argv[2:])
        sys.exit(cmd.execute())
    elif command == "add-job-to-view":
        cmd = AddJobToViewCommand(sys.argv[2:])
        sys.exit(cmd.execute())
    elif command == "copy-job":
        cmd = CopyJobCommand(sys.argv[2:])
        sys.exit(cmd.execute())
    elif command == "update-job":
        cmd = UpdateJobCommand(sys.argv[2:])
        sys.exit(cmd.execute())
    elif command == "build":
        cmd = BuildCommand(sys.argv[2:])
        sys.exit(cmd.execute())
    elif command == "stop-builds":
        cmd = StopBuildsCommand(sys.argv[2:])
        sys.exit(cmd.execute())
    elif command == "create-job":
        cmd = CreateJobCommand(sys.argv[2:])
        sys.exit(cmd.execute())
    elif command == "delete-job":
        cmd = DeleteJobCommand(sys.argv[2:])
        sys.exit(cmd.execute())
    elif command == "disable-job":
        cmd = DisableJobCommand(sys.argv[2:])
        sys.exit(cmd.execute())
    elif command == "enable-job":
        cmd = EnableJobCommand(sys.argv[2:])
        sys.exit(cmd.execute())
    elif command == "delete-builds":
        cmd = DeleteBuildsCommand(sys.argv[2:])
        sys.exit(cmd.execute())
    elif command == "groovy":
        cmd = GroovyCommand(sys.argv[2:])
        sys.exit(cmd.execute())
    elif command == "gcp":
        cmd = GCPCommand(sys.argv[2:])
        sys.exit(cmd.execute())
    elif command == "domain":
        cmd = DomainCommand(sys.argv[2:])
        sys.exit(cmd.execute())
    elif command == "prompt":
        cmd = PromptCommand(sys.argv[2:])
        sys.exit(cmd.execute())
    elif command == "help":
        cmd = HelpCommand(sys.argv[2:])
        sys.exit(cmd.execute())
    elif command == "dev-qa":
        cmd = DevQACommand(sys.argv[2:])
        sys.exit(cmd.execute())
    else:
        print(f"Error: Unknown command '{command}'", file=sys.stderr)
        print(f"Run '{program_name} help' to see available commands", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
