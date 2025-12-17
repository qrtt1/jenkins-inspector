"""Describe a specific credential command"""

import sys
import xml.etree.ElementTree as ET

from jenkins_tools.core import Command, JenkinsConfig, JenkinsCLI
from jenkins_tools.credential_describers import CREDENTIAL_DESCRIBERS


class DescribeCredentialsCommand(Command):
    """Describe a specific Jenkins credential with full details"""

    def __init__(self, args):
        """
        Initialize with command line arguments

        Args:
            args: List of command arguments (sys.argv[2:])
        """
        self.args = args
        self.show_secret = False

    def execute(self) -> int:
        """Execute describe-credentials command"""
        config = JenkinsConfig()

        # Check if credentials are configured
        if not config.is_configured():
            print("Error: Jenkins credentials not configured.", file=sys.stderr)
            print(f"Run 'jks auth' to configure credentials.", file=sys.stderr)
            return 1

        # Parse arguments
        if len(self.args) < 1:
            print("Error: Credential ID is required.", file=sys.stderr)
            print(
                "Usage: jks describe-credentials <credential-id> [--store STORE] [--show-secret]",
                file=sys.stderr,
            )
            return 1

        credential_id = self.args[0]
        store_id = "system::system::jenkins"  # Default store

        # Check for --store and --show-secret parameters
        i = 1
        while i < len(self.args):
            if self.args[i] == "--store" and i + 1 < len(self.args):
                store_id = self.args[i + 1]
                i += 2
            elif self.args[i] == "--show-secret":
                self.show_secret = True
                i += 1
            else:
                i += 1

        # Use Jenkins CLI to get credentials as XML
        cli = JenkinsCLI(config)
        result = cli.run("list-credentials-as-xml", store_id)

        if result.returncode != 0:
            print("Error: Failed to list credentials", file=sys.stderr)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            return 1

        # Parse XML
        try:
            root = ET.fromstring(result.stdout)
        except ET.ParseError as e:
            print(f"Error: Failed to parse XML: {e}", file=sys.stderr)
            return 1

        # Search for the credential in all domains
        found = False
        cred_elem = None
        domain_name = None
        domain_desc_text = ""

        for domain_creds in root.findall(
            ".//com.cloudbees.plugins.credentials.domains.DomainCredentials"
        ):
            domain_elem = domain_creds.find("domain")
            domain_name = domain_elem.find("name")
            domain_name = domain_name.text if domain_name is not None else "(global)"

            # Process credentials in this domain
            credentials_elem = domain_creds.find("credentials")
            if credentials_elem is None:
                continue

            for cred in credentials_elem:
                cred_id = cred.find("id")
                if cred_id is not None and cred_id.text == credential_id:
                    # Found the credential
                    domain_desc = domain_elem.find("description")
                    domain_desc_text = domain_desc.text if domain_desc is not None else ""
                    cred_elem = cred
                    found = True
                    break

            if found:
                break

        if not found:
            print(
                f"Error: Credential '{credential_id}' not found in store '{store_id}'",
                file=sys.stderr,
            )
            return 1

        # Print domain info
        print(f"=== Domain: {domain_name} ===")
        if domain_desc_text:
            print(f"Description: {domain_desc_text}")
        print()

        # Get credential type
        cred_type = cred_elem.tag.split(".")[-1]

        # Print basic info
        cred_id = cred_elem.find("id")
        cred_id = cred_id.text if cred_id is not None else "(no id)"

        desc = cred_elem.find("description")
        desc_text = desc.text if desc is not None and desc.text else "(no description)"

        scope = cred_elem.find("scope")
        scope_text = scope.text if scope is not None else "UNKNOWN"

        print(f"ID: {cred_id}")
        print(f"Type: {cred_type}")
        print(f"Scope: {scope_text}")
        print(f"Description: {desc_text}")
        print()

        # Get the appropriate describer
        describer = CREDENTIAL_DESCRIBERS.get(cred_type)

        if describer is None:
            # Unknown credential type
            print("Details:")
            print(f"  (Unknown credential type: {cred_type})")
            print()
            return 0

        # Get secret content if requested
        secret_data = None
        if self.show_secret:
            groovy_script = describer.get_groovy_script(credential_id)
            if groovy_script:
                result = cli.run("groovy", "=", stdin_input=groovy_script)
                if result.returncode == 0:
                    secret_data = describer.parse_secret_output(result.stdout)
            else:
                # Describer does not support secret retrieval
                print(f"Note: Secret retrieval is not supported for credential type '{cred_type}'")
                print()

        # Print credential details using describer
        describer.print_details(cred_elem, secret_data)

        return 0
