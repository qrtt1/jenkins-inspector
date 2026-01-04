"""Domain management subcommands"""

import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from xml.sax.saxutils import escape

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
    Actions: list, create, update, delete, describe
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
        if action == "create":
            return self._create(action_args)
        if action == "update":
            return self._update(action_args)
        if action == "delete":
            return self._delete(action_args)
        if action == "describe":
            return self._describe(action_args)

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
        print("  list                                                        List all credential domains")
        print("  create <name> [--description=<text>]                       Create a new credential domain")
        print("  update <name> [--description=<text>] [--new-name=<name>]  Update a credential domain")
        print("  delete <name> [--force]                                     Delete a credential domain")
        print("  describe <name>                                             Show domain details and credentials")
        print()
        print("Examples:")
        print(f"  {program_name} domain list")
        print(f"  {program_name} domain create staging --description=\"Staging credentials\" --yes-i-really-mean-it")
        print(f"  {program_name} domain update staging --description=\"Updated description\" --yes-i-really-mean-it")
        print(f"  {program_name} domain update staging --new-name=staging-v2 --yes-i-really-mean-it")
        print(f"  {program_name} domain delete staging --yes-i-really-mean-it")
        print(f"  {program_name} domain describe staging")

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

        domains, error = self._get_domains(config)
        if error:
            print("Error: Failed to list domains", file=sys.stderr)
            print(error, file=sys.stderr)
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

    def _create(self, args) -> int:
        """Create a new credential domain"""
        config = JenkinsConfig()

        if not config.is_configured():
            print("Error: Jenkins credentials not configured.", file=sys.stderr)
            print("Run 'jenkee auth' to configure credentials.", file=sys.stderr)
            return 1

        domain_name, description, error = self._parse_create_args(args)
        if error:
            print(f"Error: {error}", file=sys.stderr)
            print(
                "Usage: jenkee domain create <domain-name> "
                "[--description=<text>] [--yes-i-really-mean-it]",
                file=sys.stderr,
            )
            return 1

        if domain_name == "(global)":
            print("Error: Cannot create the global domain.", file=sys.stderr)
            return 1

        domains, list_error = self._get_domains(config)
        if list_error:
            print("Error: Failed to check existing domains", file=sys.stderr)
            print(list_error, file=sys.stderr)
            return 1

        if any(domain.name == domain_name for domain in domains):
            print(f"Error: Domain '{domain_name}' already exists.", file=sys.stderr)
            print("Run 'jenkee domain list' to see all domains.", file=sys.stderr)
            return 1

        if not self.require_confirmation(f"create domain '{domain_name}'"):
            return 0

        domain_xml = self._generate_domain_xml(domain_name, description)
        cli = JenkinsCLI(config)
        store_id = "system::system::jenkins"
        result = cli.run(
            "create-credentials-domain-by-xml",
            store_id,
            stdin_input=domain_xml,
        )

        if result.returncode != 0:
            print(f"Error: Failed to create domain '{domain_name}'", file=sys.stderr)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            return 1

        print(f"Created domain: {domain_name}")
        if description:
            print(f"  Description: {description}")
        return 0

    def _update(self, args) -> int:
        """Update a credential domain"""
        config = JenkinsConfig()

        if not config.is_configured():
            print("Error: Jenkins credentials not configured.", file=sys.stderr)
            print("Run 'jenkee auth' to configure credentials.", file=sys.stderr)
            return 1

        domain_name, new_name, description, error = self._parse_update_args(args)
        if error:
            print(f"Error: {error}", file=sys.stderr)
            print(
                "Usage: jenkee domain update <domain-name> "
                "[--description=<text>] [--new-name=<name>] [--yes-i-really-mean-it]",
                file=sys.stderr,
            )
            return 1

        if domain_name == "(global)":
            print("Error: Cannot update the global domain.", file=sys.stderr)
            return 1

        if new_name == "(global)":
            print("Error: Cannot rename to the global domain.", file=sys.stderr)
            return 1

        domains, list_error = self._get_domains(config)
        if list_error:
            print("Error: Failed to check existing domains", file=sys.stderr)
            print(list_error, file=sys.stderr)
            return 1

        current_domain = next((domain for domain in domains if domain.name == domain_name), None)
        if not current_domain:
            print(f"Error: Domain '{domain_name}' does not exist.", file=sys.stderr)
            print("Run 'jenkee domain list' to see all domains.", file=sys.stderr)
            return 1

        if new_name and new_name != domain_name:
            if any(domain.name == new_name for domain in domains):
                print(f"Error: Domain '{new_name}' already exists.", file=sys.stderr)
                print("Run 'jenkee domain list' to see all domains.", file=sys.stderr)
                return 1

        if not self.require_confirmation(f"update domain '{domain_name}'"):
            return 0

        final_name = new_name or domain_name
        final_description = current_domain.description
        if description is not None:
            final_description = description

        domain_xml = self._generate_domain_xml(final_name, final_description)
        cli = JenkinsCLI(config)
        store_id = "system::system::jenkins"
        result = cli.run(
            "update-credentials-domain-by-xml",
            store_id,
            domain_name,
            stdin_input=domain_xml,
        )

        if result.returncode != 0:
            print(f"Error: Failed to update domain '{domain_name}'", file=sys.stderr)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            return 1

        print(f"Updated domain: {final_name}")
        if new_name and new_name != domain_name:
            print(f"  Previous name: {domain_name}")
        if description is not None:
            print(f"  Description: {final_description}")
        return 0

    def _delete(self, args) -> int:
        """Delete a credential domain"""
        config = JenkinsConfig()

        if not config.is_configured():
            print("Error: Jenkins credentials not configured.", file=sys.stderr)
            print("Run 'jenkee auth' to configure credentials.", file=sys.stderr)
            return 1

        domain_name, force, error = self._parse_delete_args(args)
        if error:
            print(f"Error: {error}", file=sys.stderr)
            print(
                "Usage: jenkee domain delete <domain-name> "
                "[--yes-i-really-mean-it] [--force]",
                file=sys.stderr,
            )
            return 1

        if domain_name == "(global)":
            print("Error: Cannot delete the global domain.", file=sys.stderr)
            return 1

        domains, list_error = self._get_domains(config)
        if list_error:
            print("Error: Failed to check existing domains", file=sys.stderr)
            print(list_error, file=sys.stderr)
            return 1

        current_domain = next((domain for domain in domains if domain.name == domain_name), None)
        if not current_domain:
            print(f"Error: Domain '{domain_name}' does not exist.", file=sys.stderr)
            print("Run 'jenkee domain list' to see all domains.", file=sys.stderr)
            return 1

        credentials, cred_error = self._get_domain_credentials(config, domain_name)
        if cred_error:
            print("Error: Failed to check domain credentials", file=sys.stderr)
            print(cred_error, file=sys.stderr)
            return 1

        credential_count = current_domain.credential_count
        if credential_count > 0 and not force:
            print(f"Warning: Domain '{domain_name}' contains {credential_count} credentials.")
            print()
            print("Credentials in this domain:")
            for cred_id, _cred_type in credentials:
                print(f"  - {cred_id}")
            if not credentials:
                print("  (credential details unavailable)")
            print()
            print("Deleting this domain will also delete all credentials in it.")
            print("To proceed, add the --force flag:")
            print(f"  jenkee domain delete {domain_name} --yes-i-really-mean-it --force")
            return 1

        if not self.require_confirmation(f"delete domain '{domain_name}'"):
            return 0

        cli = JenkinsCLI(config)
        store_id = "system::system::jenkins"
        result = cli.run("delete-credentials-domain", store_id, domain_name)

        if result.returncode != 0:
            print(f"Error: Failed to delete domain '{domain_name}'", file=sys.stderr)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            return 1

        print(f"Deleted domain: {domain_name}")
        return 0

    def _describe(self, args) -> int:
        """Describe a credential domain"""
        config = JenkinsConfig()

        if not config.is_configured():
            print("Error: Jenkins credentials not configured.", file=sys.stderr)
            print("Run 'jenkee auth' to configure credentials.", file=sys.stderr)
            return 1

        if len(args) != 1:
            print("Error: Domain name is required.", file=sys.stderr)
            print("Usage: jenkee domain describe <domain-name>", file=sys.stderr)
            return 1

        domain_name = args[0]

        domains, list_error = self._get_domains(config)
        if list_error:
            print("Error: Failed to check existing domains", file=sys.stderr)
            print(list_error, file=sys.stderr)
            return 1

        current_domain = next((domain for domain in domains if domain.name == domain_name), None)
        if not current_domain:
            print(f"Error: Domain '{domain_name}' does not exist.", file=sys.stderr)
            print("Run 'jenkee domain list' to see all domains.", file=sys.stderr)
            return 1

        credentials, cred_error = self._get_domain_credentials(config, domain_name)
        if cred_error:
            print("Error: Failed to describe domain", file=sys.stderr)
            print(cred_error, file=sys.stderr)
            return 1

        description = current_domain.description.strip()
        if not description:
            if domain_name == "(global)":
                description = "Global credentials domain"
            else:
                description = "(no description)"

        print(f"=== Domain: {domain_name} ===")
        print(f"Name: {domain_name}")
        print(f"Description: {description}")
        print(f"Credentials: {len(credentials)}")
        print()
        print("Credentials in this domain:")
        if not credentials:
            print("  (no credentials)")
            return 0

        for cred_id, cred_type in credentials:
            print(f"  - {cred_id} ({cred_type})")
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

    def _generate_domain_xml(self, name: str, description: str) -> str:
        """Generate XML payload for domain create/update"""
        safe_name = escape(name)
        safe_description = escape(description or "")
        return (
            "<com.cloudbees.plugins.credentials.domains.Domain>"
            f"<name>{safe_name}</name>"
            f"<description>{safe_description}</description>"
            "<specifications/>"
            "</com.cloudbees.plugins.credentials.domains.Domain>"
        )

    def _get_domains(self, config: JenkinsConfig) -> tuple[list[DomainInfo], str | None]:
        """Fetch domain metadata from Jenkins"""
        cli = JenkinsCLI(config)
        groovy_script = self._generate_list_script()
        result = cli.run("groovy", "=", stdin_input=groovy_script)

        if result.returncode != 0:
            return [], result.stderr or result.stdout or "Unknown error"

        try:
            domains = self._parse_domain_list(result.stdout)
        except ValueError as exc:
            return [], f"Failed to parse domain list output: {exc}"

        return domains, None

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

    def _parse_create_args(self, args) -> tuple[str | None, str, str | None]:
        """Parse domain create arguments"""
        domain_name = None
        description = ""

        i = 0
        while i < len(args):
            arg = args[i]
            if arg.startswith("--description="):
                description = arg.split("=", 1)[1]
            elif arg == "--description":
                if i + 1 >= len(args):
                    return None, "", "--description requires a value"
                description = args[i + 1]
                i += 1
            elif arg.startswith("--"):
                return None, "", f"Unknown option: {arg}"
            elif domain_name is None:
                domain_name = arg
            else:
                return None, "", f"Unexpected argument: {arg}"
            i += 1

        if not domain_name:
            return None, "", "Missing domain name"

        return domain_name, description, None

    def _parse_update_args(self, args) -> tuple[str | None, str | None, str | None, str | None]:
        """Parse domain update arguments"""
        domain_name = None
        new_name = None
        description = None

        i = 0
        while i < len(args):
            arg = args[i]
            if arg.startswith("--description="):
                description = arg.split("=", 1)[1]
            elif arg == "--description":
                if i + 1 >= len(args):
                    return None, None, None, "--description requires a value"
                description = args[i + 1]
                i += 1
            elif arg.startswith("--new-name="):
                new_name = arg.split("=", 1)[1]
            elif arg == "--new-name":
                if i + 1 >= len(args):
                    return None, None, None, "--new-name requires a value"
                new_name = args[i + 1]
                i += 1
            elif arg.startswith("--"):
                return None, None, None, f"Unknown option: {arg}"
            elif domain_name is None:
                domain_name = arg
            else:
                return None, None, None, f"Unexpected argument: {arg}"
            i += 1

        if not domain_name:
            return None, None, None, "Missing domain name"

        if new_name is not None and new_name == "":
            return None, None, None, "New domain name cannot be empty"

        if description is None and new_name is None:
            return None, None, None, "No updates provided"

        return domain_name, new_name, description, None

    def _parse_delete_args(self, args) -> tuple[str | None, bool, str | None]:
        """Parse domain delete arguments"""
        domain_name = None
        force = False

        i = 0
        while i < len(args):
            arg = args[i]
            if arg == "--force":
                force = True
            elif arg.startswith("--"):
                return None, False, f"Unknown option: {arg}"
            elif domain_name is None:
                domain_name = arg
            else:
                return None, False, f"Unexpected argument: {arg}"
            i += 1

        if not domain_name:
            return None, False, "Missing domain name"

        return domain_name, force, None

    def _get_domain_credentials(
        self,
        config: JenkinsConfig,
        domain_name: str,
    ) -> tuple[list[tuple[str, str]], str | None]:
        """Fetch credential IDs and types for a specific domain"""
        cli = JenkinsCLI(config)
        store_id = "system::system::jenkins"
        result = cli.run("list-credentials-as-xml", store_id)

        if result.returncode != 0:
            return [], result.stderr or result.stdout or "Unknown error"

        try:
            root = ET.fromstring(result.stdout)
        except ET.ParseError as exc:
            return [], f"Failed to parse credentials XML: {exc}"

        for domain_creds in root.findall(
            ".//com.cloudbees.plugins.credentials.domains.DomainCredentials"
        ):
            domain_elem = domain_creds.find("domain")
            if domain_elem is None:
                continue
            name_elem = domain_elem.find("name")
            name = name_elem.text if name_elem is not None else "(global)"
            if name != domain_name:
                continue

            credentials = []
            credentials_elem = domain_creds.find("credentials")
            if credentials_elem is None:
                return [], None

            for cred in credentials_elem:
                cred_id = cred.find("id")
                cred_id_text = cred_id.text if cred_id is not None else "(no id)"
                cred_type = cred.tag.split(".")[-1]
                credentials.append((cred_id_text, cred_type))

            return credentials, None

        return [], None
