"""Domain management subcommands"""

import sys
from dataclasses import dataclass
from pathlib import Path

from jenkins_tools.core import Command, DangerousCommandMixin, JenkinsConfig, JenkinsCLI


@dataclass
class DomainInfo:
    """Domain metadata for display"""
    name: str
    description: str
    credential_count: int


class DomainCommand(DangerousCommandMixin, Command):
    """
    Domain management command dispatcher

    Handles: jenkee domain <action> [args...]
    Actions: list
    """

    def __init__(self, args=None):
        """
        Initialize with command line arguments

        Args:
            args: List of command arguments (after 'domain')
        """
        self.args = args or []
        super().__init__()

    def execute(self) -> int:
        """Execute domain subcommand"""
        if len(self.args) == 0 or self.args[0] in ("--help", "-h"):
            self._show_help()
            return 0

        action = self.args[0]
        action_args = self.args[1:]

        if action == "list":
            return self._list(action_args)

        program_name = Path(sys.argv[0]).name if sys.argv else "jenkee"
        print(f"Error: Unknown domain action '{action}'", file=sys.stderr)
        print(f"Run '{program_name} domain --help' to see available actions", file=sys.stderr)
        return 1

    def _show_help(self):
        """Show domain management help"""
        program_name = Path(sys.argv[0]).name if sys.argv else "jenkee"
        print(f"Usage: {program_name} domain <action> [options]")
        print()
        print("Actions:")
        print()
        print("  list                           List all credential domains")
        print()
        print("Examples:")
        print(f"  {program_name} domain list")

    def _list(self, args) -> int:
        """List all credentials domains"""
        config = JenkinsConfig()

        if not config.is_configured():
            print("Error: Jenkins credentials not configured.", file=sys.stderr)
            print("Run 'jenkee auth' to configure credentials.", file=sys.stderr)
            return 1

        if args:
            print("Error: domain list does not accept extra arguments.", file=sys.stderr)
            print("Usage: jenkee domain list", file=sys.stderr)
            return 1

        cli = JenkinsCLI(config)
        groovy_script = self._generate_list_script()
        result = cli.run("groovy", "=", stdin_input=groovy_script)

        if result.returncode != 0:
            print("Error: Failed to list domains", file=sys.stderr)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            return 1

        try:
            domains = self._parse_domain_list(result.stdout)
        except ValueError as exc:
            print(f"Error: Failed to parse domain list output: {exc}", file=sys.stderr)
            if result.stdout:
                print(result.stdout, file=sys.stderr)
            return 1

        if not domains:
            print("No domains found.")
            return 0

        name_width = max(len(domain.name) for domain in domains)

        print("Available domains:")
        for domain in domains:
            description = domain.description.strip()
            if not description:
                if domain.name == "(global)":
                    description = "Global credentials domain"
                else:
                    description = "(no description)"

            credential_label = "credential" if domain.credential_count == 1 else "credentials"
            print(
                f"  {domain.name:<{name_width}}  "
                f"{description} ({domain.credential_count} {credential_label})"
            )

        print()
        print(f"Total: {len(domains)} domains")
        return 0

    def _generate_list_script(self) -> str:
        """Generate Groovy script for listing domains and credential counts"""
        return """
import com.cloudbees.plugins.credentials.SystemCredentialsProvider

def store = SystemCredentialsProvider.getInstance().getStore()
store.getDomains().each { domain ->
    def name = domain.getName()
    if (name == null) {
        name = "(global)"
    }
    def desc = domain.getDescription()
    if (desc == null) {
        desc = ""
    }
    def creds = store.getCredentials(domain)
    def count = creds != null ? creds.size() : 0
    println("${name}\\t${desc}\\t${count}")
}
"""

    def _parse_domain_list(self, stdout: str) -> list[DomainInfo]:
        """Parse Groovy output into domain metadata"""
        domains = []

        for line in stdout.splitlines():
            if not line.strip():
                continue
            parts = line.split("\t")
            if len(parts) < 3:
                raise ValueError("unexpected line format")

            name = parts[0].strip()
            description = parts[1]
            try:
                count = int(parts[2].strip())
            except ValueError as exc:
                raise ValueError("invalid credential count") from exc

            domains.append(
                DomainInfo(
                    name=name,
                    description=description,
                    credential_count=count,
                )
            )

        return domains
