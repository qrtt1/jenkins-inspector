"""Jenkins CLI commands"""

from jenkins_tools.commands.auth import AuthCommand
from jenkins_tools.commands.list_views import ListViewsCommand
from jenkins_tools.commands.list_jobs import ListJobsCommand
from jenkins_tools.commands.get_job import GetJobCommand
from jenkins_tools.commands.list_builds import ListBuildsCommand
from jenkins_tools.commands.console import ConsoleCommand
from jenkins_tools.commands.job_status import JobStatusCommand
from jenkins_tools.commands.job_diff import JobDiffCommand
from jenkins_tools.commands.list_credentials import ListCredentialsCommand
from jenkins_tools.commands.describe_credentials import DescribeCredentialsCommand
from jenkins_tools.commands.add_job_to_view import AddJobToViewCommand
from jenkins_tools.commands.copy_job import CopyJobCommand
from jenkins_tools.commands.update_job import UpdateJobCommand
from jenkins_tools.commands.build import BuildCommand
from jenkins_tools.commands.stop_builds import StopBuildsCommand
from jenkins_tools.commands.create_job import CreateJobCommand
from jenkins_tools.commands.delete_job import DeleteJobCommand
from jenkins_tools.commands.disable_job import DisableJobCommand
from jenkins_tools.commands.enable_job import EnableJobCommand
from jenkins_tools.commands.delete_builds import DeleteBuildsCommand
from jenkins_tools.commands.groovy import GroovyCommand
from jenkins_tools.commands.domain import DomainCommand
from jenkins_tools.commands.help import HelpCommand
from jenkins_tools.commands.prompt import PromptCommand
from jenkins_tools.commands.dev_qa import DevQACommand

__all__ = [
    "AuthCommand",
    "ListViewsCommand",
    "ListJobsCommand",
    "GetJobCommand",
    "ListBuildsCommand",
    "ConsoleCommand",
    "JobStatusCommand",
    "JobDiffCommand",
    "ListCredentialsCommand",
    "DescribeCredentialsCommand",
    "AddJobToViewCommand",
    "CopyJobCommand",
    "UpdateJobCommand",
    "BuildCommand",
    "StopBuildsCommand",
    "CreateJobCommand",
    "DeleteJobCommand",
    "DisableJobCommand",
    "EnableJobCommand",
    "DeleteBuildsCommand",
    "GroovyCommand",
    "DomainCommand",
    "HelpCommand",
    "PromptCommand",
    "DevQACommand",
]
