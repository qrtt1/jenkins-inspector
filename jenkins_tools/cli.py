"""Jenkins CLI main entry point"""

import os
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
    DevQACommand,
    ProfileCommand,
)
from jenkins_tools.commands.gcp import GCPCommand


def _extract_profile_flag(argv: list[str]) -> list[str]:
    """
    Pull a global `--profile <name>` flag out of argv, wherever it appears,
    and apply it as JENKEE_PROFILE for this process.

    This keeps every existing Command unaware of --profile entirely:
    JenkinsConfig already reads JENKEE_PROFILE from the environment, so a
    CLI flag and an exported env var end up on the exact same code path.
    """
    result = []
    i = 0
    while i < len(argv):
        if argv[i] == "--profile":
            if i + 1 >= len(argv):
                print("Error: --profile requires a value", file=sys.stderr)
                sys.exit(1)
            os.environ["JENKEE_PROFILE"] = argv[i + 1]
            i += 2
            continue
        result.append(argv[i])
        i += 1
    return result


def main():
    """Main entry point for CLI command"""
    program_name = Path(sys.argv[0]).name if sys.argv else "jenkee"

    argv = _extract_profile_flag(sys.argv[1:])

    if len(argv) < 1:
        # 沒有參數時顯示命令列表
        cmd = HelpCommand()
        sys.exit(cmd.execute())

    command = argv[0]

    # Handle global --help or -h flag
    if command in ("--help", "-h"):
        cmd = HelpCommand(argv[1:])
        sys.exit(cmd.execute())

    # Dispatch to appropriate command
    if command == "auth":
        cmd = AuthCommand()
        sys.exit(cmd.execute())
    elif command == "list-views":
        cmd = ListViewsCommand()
        sys.exit(cmd.execute())
    elif command == "list-jobs":
        cmd = ListJobsCommand(argv[1:])
        sys.exit(cmd.execute())
    elif command == "get-job":
        cmd = GetJobCommand(argv[1:])
        sys.exit(cmd.execute())
    elif command == "list-builds":
        cmd = ListBuildsCommand(argv[1:])
        sys.exit(cmd.execute())
    elif command == "console":
        cmd = ConsoleCommand(argv[1:])
        sys.exit(cmd.execute())
    elif command == "job-status":
        cmd = JobStatusCommand(argv[1:])
        sys.exit(cmd.execute())
    elif command == "job-diff":
        cmd = JobDiffCommand(argv[1:])
        sys.exit(cmd.execute())
    elif command == "list-credentials":
        cmd = ListCredentialsCommand(argv[1:])
        sys.exit(cmd.execute())
    elif command == "describe-credentials":
        cmd = DescribeCredentialsCommand(argv[1:])
        sys.exit(cmd.execute())
    elif command == "add-job-to-view":
        cmd = AddJobToViewCommand(argv[1:])
        sys.exit(cmd.execute())
    elif command == "copy-job":
        cmd = CopyJobCommand(argv[1:])
        sys.exit(cmd.execute())
    elif command == "update-job":
        cmd = UpdateJobCommand(argv[1:])
        sys.exit(cmd.execute())
    elif command == "build":
        cmd = BuildCommand(argv[1:])
        sys.exit(cmd.execute())
    elif command == "stop-builds":
        cmd = StopBuildsCommand(argv[1:])
        sys.exit(cmd.execute())
    elif command == "create-job":
        cmd = CreateJobCommand(argv[1:])
        sys.exit(cmd.execute())
    elif command == "delete-job":
        cmd = DeleteJobCommand(argv[1:])
        sys.exit(cmd.execute())
    elif command == "disable-job":
        cmd = DisableJobCommand(argv[1:])
        sys.exit(cmd.execute())
    elif command == "enable-job":
        cmd = EnableJobCommand(argv[1:])
        sys.exit(cmd.execute())
    elif command == "delete-builds":
        cmd = DeleteBuildsCommand(argv[1:])
        sys.exit(cmd.execute())
    elif command == "groovy":
        cmd = GroovyCommand(argv[1:])
        sys.exit(cmd.execute())
    elif command == "gcp":
        cmd = GCPCommand(argv[1:])
        sys.exit(cmd.execute())
    elif command == "domain":
        cmd = DomainCommand(argv[1:])
        sys.exit(cmd.execute())
    elif command == "profile":
        cmd = ProfileCommand(argv[1:])
        sys.exit(cmd.execute())
    elif command == "help":
        cmd = HelpCommand(argv[1:])
        sys.exit(cmd.execute())
    elif command == "dev-qa":
        cmd = DevQACommand(argv[1:])
        sys.exit(cmd.execute())
    else:
        print(f"Error: Unknown command '{command}'", file=sys.stderr)
        print(f"Run '{program_name} help' to see available commands", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
