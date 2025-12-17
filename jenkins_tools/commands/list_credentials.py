"""List credentials command"""

import sys
import xml.etree.ElementTree as ET

from jenkins_tools.core import Command, JenkinsConfig, JenkinsCLI


class ListCredentialsCommand(Command):
    """List Jenkins credentials with metadata"""

    def __init__(self, args):
        """
        Initialize with command line arguments

        Args:
            args: List of command arguments (sys.argv[2:])
        """
        self.args = args

    def execute(self) -> int:
        """Execute list-credentials command"""
        config = JenkinsConfig()

        # Check if credentials are configured
        if not config.is_configured():
            print("Error: Jenkins credentials not configured.", file=sys.stderr)
            print(f"Run 'jks auth' to configure credentials.", file=sys.stderr)
            return 1

        # Parse arguments
        store_id = "system::system::jenkins"  # Default store
        domain_filter = None

        # Check for --store parameter
        i = 0
        while i < len(self.args):
            if self.args[i] == "--store" and i + 1 < len(self.args):
                store_id = self.args[i + 1]
                i += 2
            else:
                # First positional argument is domain filter
                if domain_filter is None:
                    domain_filter = self.args[i]
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

        # Process domains
        for domain_creds in root.findall(
            ".//com.cloudbees.plugins.credentials.domains.DomainCredentials"
        ):
            domain_elem = domain_creds.find("domain")
            domain_name = domain_elem.find("name")
            domain_name = domain_name.text if domain_name is not None else "(global)"

            # Filter by domain if specified
            if domain_filter and domain_name != domain_filter:
                continue

            domain_desc = domain_elem.find("description")
            domain_desc_text = domain_desc.text if domain_desc is not None else ""

            # Print domain header
            print(f"\n=== Domain: {domain_name} ===")
            if domain_desc_text:
                print(f"Description: {domain_desc_text}")
            print()

            # Process credentials in this domain
            credentials_elem = domain_creds.find("credentials")
            if credentials_elem is None:
                print("  (no credentials)")
                continue

            cred_count = 0
            for cred in credentials_elem:
                cred_count += 1
                self._print_credential(cred)

            if cred_count == 0:
                print("  (no credentials)")

        return 0

    def _print_credential(self, cred_elem):
        """Print credential information"""
        # Get credential type from tag name
        cred_type = cred_elem.tag.split(".")[-1]

        # Common fields
        cred_id = cred_elem.find("id")
        cred_id = cred_id.text if cred_id is not None else "(no id)"

        desc = cred_elem.find("description")
        desc_text = desc.text if desc is not None and desc.text else "(no description)"

        scope = cred_elem.find("scope")
        scope_text = scope.text if scope is not None else "UNKNOWN"

        # Print basic info
        print(f"ID: {cred_id}")
        print(f"  Type: {cred_type}")
        print(f"  Scope: {scope_text}")
        print(f"  Description: {desc_text}")

        # Type-specific fields
        if cred_type == "FileCredentialsImpl":
            filename = cred_elem.find("fileName")
            if filename is not None:
                print(f"  File Name: {filename.text}")

        elif cred_type == "BasicSSHUserPrivateKey":
            username = cred_elem.find("username")
            if username is not None:
                print(f"  Username: {username.text}")

        elif cred_type == "UsernamePasswordCredentialsImpl":
            username = cred_elem.find("username")
            if username is not None:
                print(f"  Username: {username.text}")

        elif cred_type == "StringCredentialsImpl":
            # Secret text - no additional info
            pass

        elif cred_type == "GoogleRobotPrivateKeyCredentials":
            project_id = cred_elem.find("projectId")
            if project_id is not None:
                print(f"  Project ID: {project_id.text}")

        elif cred_type == "AzureStorageAccount":
            storage_data = cred_elem.find("storageData")
            if storage_data is not None:
                account_name = storage_data.find("storageAccountName")
                if account_name is not None:
                    print(f"  Storage Account: {account_name.text}")

        elif cred_type == "BrowserStackCredentials":
            username = cred_elem.find("username")
            if username is not None:
                print(f"  Username: {username.text}")

        print()  # Blank line between credentials
