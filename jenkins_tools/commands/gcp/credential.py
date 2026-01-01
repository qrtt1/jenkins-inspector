"""GCP credential management subcommands"""

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from jenkins_tools.core import Command, JenkinsConfig, JenkinsCLI
from jenkins_tools.credential_describers import CREDENTIAL_DESCRIBERS


class CredentialCommand(Command):
    """
    GCP credential management command dispatcher

    Handles: jenkee gcp credential <action> [args...]
    Actions: create, list, describe, update, delete
    """

    def __init__(self, args):
        """
        Initialize with command line arguments

        Args:
            args: List of command arguments (after 'gcp credential')
        """
        self.args = args

    def execute(self) -> int:
        """Execute credential subcommand"""
        if len(self.args) == 0 or self.args[0] in ("--help", "-h"):
            self._show_help()
            return 0

        action = self.args[0]
        action_args = self.args[1:]

        # Dispatch to appropriate action handler
        if action == "create":
            return self._create(action_args)
        elif action == "list":
            return self._list(action_args)
        elif action == "describe":
            return self._describe(action_args)
        elif action == "update":
            return self._update(action_args)
        elif action == "delete":
            return self._delete(action_args)
        else:
            program_name = Path(sys.argv[0]).name if sys.argv else "jenkee"
            print(f"Error: Unknown credential action '{action}'", file=sys.stderr)
            print(f"Run '{program_name} gcp credential --help' to see available actions", file=sys.stderr)
            return 1

    def _show_help(self):
        """Show credential management help"""
        program_name = Path(sys.argv[0]).name if sys.argv else "jenkee"
        print(f"Usage: {program_name} gcp credential <action> [options]")
        print()
        print("Actions:")
        print()
        print("  create <id> <json-key-file>    Create a new GCP credential")
        print("  list                           List all GCP credentials")
        print("  describe <id> [--show-secret]  Show detailed credential information")
        print("  update <id> <json-key-file>    Update an existing GCP credential")
        print("  delete <id> [--confirm]        Delete a GCP credential")
        print()
        print("Examples:")
        print(f"  {program_name} gcp credential create my-gcp-sa ~/key.json")
        print(f"  {program_name} gcp credential list")
        print(f"  {program_name} gcp credential describe my-gcp-sa")
        print(f"  {program_name} gcp credential describe my-gcp-sa --show-secret")
        print(f"  {program_name} gcp credential update my-gcp-sa ~/new-key.json")
        print(f"  {program_name} gcp credential delete my-gcp-sa --confirm")

    def _create(self, args) -> int:
        """Create a new GCP credential"""
        config = JenkinsConfig()

        # Check if credentials are configured
        if not config.is_configured():
            print("Error: Jenkins credentials not configured.", file=sys.stderr)
            print(f"Run 'jenkee auth' to configure credentials.", file=sys.stderr)
            return 1

        # Parse arguments
        if len(args) < 2:
            print("Error: Credential ID and JSON key file path are required.", file=sys.stderr)
            program_name = Path(sys.argv[0]).name if sys.argv else "jenkee"
            print(
                f"Usage: {program_name} gcp credential create <credential-id> <json-key-file>",
                file=sys.stderr,
            )
            return 1

        credential_id = args[0]
        json_key_path = args[1]

        # Validate JSON key file
        key_file = Path(json_key_path)
        if not key_file.exists():
            print(f"Error: JSON key file not found: {json_key_path}", file=sys.stderr)
            return 1

        # Read and validate JSON content
        try:
            with open(key_file, 'r') as f:
                key_data = json.load(f)
                # Basic validation
                required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email']
                missing_fields = [field for field in required_fields if field not in key_data]
                if missing_fields:
                    print(f"Error: Invalid service account key. Missing fields: {', '.join(missing_fields)}", file=sys.stderr)
                    return 1
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON file: {e}", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"Error: Failed to read JSON key file: {e}", file=sys.stderr)
            return 1

        # Read raw JSON content for Jenkins
        with open(key_file, 'r') as f:
            json_content = f.read()

        # Create Groovy script to create the credential using FileCredentialsImpl
        groovy_script = self._generate_create_script(credential_id, json_content, key_data['project_id'])

        # Execute via Jenkins CLI
        cli = JenkinsCLI(config)
        result = cli.run("groovy", "=", stdin_input=groovy_script)

        if result.returncode != 0:
            print("Error: Failed to create GCP credential.", file=sys.stderr)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            return 1

        # Parse output
        output = result.stdout
        if "SUCCESS" in output:
            print(f"Created GCP credential: {credential_id}")
            print(f"  Project ID: {key_data['project_id']}")
            print(f"  Service Account: {key_data['client_email']}")
            return 0
        elif "ALREADY_EXISTS" in output:
            print(f"Error: Credential '{credential_id}' already exists.", file=sys.stderr)
            print("Use 'update' action or delete the existing credential first.", file=sys.stderr)
            return 1
        else:
            print("Error: Unexpected response from Jenkins.", file=sys.stderr)
            print(output, file=sys.stderr)
            return 1

    def _list(self, args) -> int:
        """List all GCP credentials"""
        config = JenkinsConfig()

        if not config.is_configured():
            print("Error: Jenkins credentials not configured.", file=sys.stderr)
            print(f"Run 'jenkee auth' to configure credentials.", file=sys.stderr)
            return 1

        # Use Jenkins CLI to get credentials as XML
        cli = JenkinsCLI(config)
        store_id = "system::system::jenkins"
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

        # Find GCP credentials (FileCredentialsImpl with GCP-related description/filename)
        found_any = False
        for domain_creds in root.findall(
            ".//com.cloudbees.plugins.credentials.domains.DomainCredentials"
        ):
            credentials_elem = domain_creds.find("credentials")
            if credentials_elem is None:
                continue

            for cred in credentials_elem:
                cred_type = cred.tag.split(".")[-1]

                # Look for FileCredentialsImpl (Secret file) - our GCP credentials
                if cred_type == "FileCredentialsImpl":
                    cred_id = cred.find("id")
                    if cred_id is not None:
                        cred_id_text = cred_id.text

                        # Try to identify if this is a GCP credential
                        # We'll fetch additional info via groovy script
                        file_name = cred.find("fileName")
                        file_name_text = file_name.text if file_name is not None else ""

                        desc = cred.find("description")
                        desc_text = desc.text if desc is not None and desc.text else ""

                        if not found_any:
                            print("GCP Service Account Credentials:")
                            print()
                            found_any = True

                        print(f"ID: {cred_id_text}")
                        print(f"  Type: Secret file (FileCredentialsImpl)")
                        if file_name_text:
                            print(f"  File Name: {file_name_text}")
                        if desc_text:
                            print(f"  Description: {desc_text}")
                        print()

        if not found_any:
            print("No GCP credentials found.")
            print()
            program_name = Path(sys.argv[0]).name if sys.argv else "jenkee"
            print(f"Create one with: {program_name} gcp credential create <id> <json-key-file>")

        return 0

    def _describe(self, args) -> int:
        """Describe a specific GCP credential"""
        config = JenkinsConfig()

        if not config.is_configured():
            print("Error: Jenkins credentials not configured.", file=sys.stderr)
            print(f"Run 'jenkee auth' to configure credentials.", file=sys.stderr)
            return 1

        # Parse arguments
        if len(args) < 1:
            print("Error: Credential ID is required.", file=sys.stderr)
            program_name = Path(sys.argv[0]).name if sys.argv else "jenkee"
            print(
                f"Usage: {program_name} gcp credential describe <credential-id> [--show-secret]",
                file=sys.stderr,
            )
            return 1

        credential_id = args[0]
        show_secret = "--show-secret" in args

        # Get credential details via groovy script
        cli = JenkinsCLI(config)
        groovy_script = self._generate_describe_script(credential_id, show_secret)
        result = cli.run("groovy", "=", stdin_input=groovy_script)

        if result.returncode != 0:
            print("Error: Failed to describe credential", file=sys.stderr)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            return 1

        output = result.stdout
        if "NOT_FOUND" in output:
            print(f"Error: Credential '{credential_id}' not found.", file=sys.stderr)
            return 1
        elif "SUCCESS" in output:
            # Print the output (groovy script formats it)
            print(output.replace("SUCCESS\n", ""))
            return 0
        else:
            print("Error: Unexpected response from Jenkins.", file=sys.stderr)
            print(output, file=sys.stderr)
            return 1

    def _update(self, args) -> int:
        """Update an existing GCP credential"""
        config = JenkinsConfig()

        if not config.is_configured():
            print("Error: Jenkins credentials not configured.", file=sys.stderr)
            print(f"Run 'jenkee auth' to configure credentials.", file=sys.stderr)
            return 1

        # Parse arguments
        if len(args) < 2:
            print("Error: Credential ID and JSON key file path are required.", file=sys.stderr)
            program_name = Path(sys.argv[0]).name if sys.argv else "jenkee"
            print(
                f"Usage: {program_name} gcp credential update <credential-id> <json-key-file>",
                file=sys.stderr,
            )
            return 1

        credential_id = args[0]
        json_key_path = args[1]

        # Validate JSON key file
        key_file = Path(json_key_path)
        if not key_file.exists():
            print(f"Error: JSON key file not found: {json_key_path}", file=sys.stderr)
            return 1

        # Read and validate JSON content
        try:
            with open(key_file, 'r') as f:
                key_data = json.load(f)
                required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email']
                missing_fields = [field for field in required_fields if field not in key_data]
                if missing_fields:
                    print(f"Error: Invalid service account key. Missing fields: {', '.join(missing_fields)}", file=sys.stderr)
                    return 1
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON file: {e}", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"Error: Failed to read JSON key file: {e}", file=sys.stderr)
            return 1

        # Read raw JSON content for Jenkins
        with open(key_file, 'r') as f:
            json_content = f.read()

        # Create Groovy script to update the credential
        groovy_script = self._generate_update_script(credential_id, json_content, key_data['project_id'])

        # Execute via Jenkins CLI
        cli = JenkinsCLI(config)
        result = cli.run("groovy", "=", stdin_input=groovy_script)

        if result.returncode != 0:
            print("Error: Failed to update GCP credential.", file=sys.stderr)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            return 1

        # Parse output
        output = result.stdout
        if "SUCCESS" in output:
            print(f"Updated GCP credential: {credential_id}")
            print(f"  Project ID: {key_data['project_id']}")
            print(f"  Service Account: {key_data['client_email']}")
            return 0
        elif "NOT_FOUND" in output:
            print(f"Error: Credential '{credential_id}' not found.", file=sys.stderr)
            program_name = Path(sys.argv[0]).name if sys.argv else "jenkee"
            print(f"Create it first with: {program_name} gcp credential create {credential_id} {json_key_path}", file=sys.stderr)
            return 1
        else:
            print("Error: Unexpected response from Jenkins.", file=sys.stderr)
            print(output, file=sys.stderr)
            return 1

    def _delete(self, args) -> int:
        """Delete a GCP credential"""
        config = JenkinsConfig()

        if not config.is_configured():
            print("Error: Jenkins credentials not configured.", file=sys.stderr)
            print(f"Run 'jenkee auth' to configure credentials.", file=sys.stderr)
            return 1

        # Parse arguments
        if len(args) < 1:
            print("Error: Credential ID is required.", file=sys.stderr)
            program_name = Path(sys.argv[0]).name if sys.argv else "jenkee"
            print(
                f"Usage: {program_name} gcp credential delete <credential-id> [--confirm]",
                file=sys.stderr,
            )
            return 1

        credential_id = args[0]
        has_confirm = "--confirm" in args

        # Interactive confirmation if --confirm not provided
        if not has_confirm:
            try:
                response = input(f"Are you sure you want to delete credential '{credential_id}'? (y/N): ")
                if response.lower() not in ('y', 'yes'):
                    print("Deletion cancelled.")
                    return 0
            except (EOFError, KeyboardInterrupt):
                print("\nDeletion cancelled.")
                return 0

        # Create Groovy script to delete the credential
        groovy_script = self._generate_delete_script(credential_id)

        # Execute via Jenkins CLI
        cli = JenkinsCLI(config)
        result = cli.run("groovy", "=", stdin_input=groovy_script)

        if result.returncode != 0:
            print("Error: Failed to delete GCP credential.", file=sys.stderr)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            return 1

        # Parse output
        output = result.stdout
        if "SUCCESS" in output:
            print(f"Deleted GCP credential: {credential_id}")
            return 0
        elif "NOT_FOUND" in output:
            print(f"Error: Credential '{credential_id}' not found.", file=sys.stderr)
            return 1
        else:
            print("Error: Unexpected response from Jenkins.", file=sys.stderr)
            print(output, file=sys.stderr)
            return 1

    def _generate_create_script(self, credential_id: str, json_content: str, project_id: str) -> str:
        """Generate Groovy script to create GCP credential using FileCredentialsImpl"""
        # Escape single quotes in JSON content
        escaped_json = json_content.replace("'", "\\'").replace("\n", "\\n")

        return f"""
import com.cloudbees.plugins.credentials.CredentialsProvider
import com.cloudbees.plugins.credentials.CredentialsScope
import com.cloudbees.plugins.credentials.domains.Domain
import org.jenkinsci.plugins.plaincredentials.impl.FileCredentialsImpl
import com.cloudbees.plugins.credentials.SecretBytes
import jenkins.model.Jenkins

def jenkins = Jenkins.get()
def domain = Domain.global()
def store = jenkins.getExtensionList('com.cloudbees.plugins.credentials.SystemCredentialsProvider')[0].getStore()

def credId = '{credential_id}'
def jsonKey = '''{escaped_json}'''

// Check if credential already exists
def existing = CredentialsProvider.lookupCredentials(
    com.cloudbees.plugins.credentials.Credentials.class,
    jenkins,
    null,
    null
).find {{ it.id == credId }}

if (existing != null) {{
    println "ALREADY_EXISTS"
    return
}}

try {{
    // Create SecretBytes from JSON content
    def jsonKeyBytes = SecretBytes.fromBytes(jsonKey.getBytes('UTF-8'))

    // Create FileCredentialsImpl (Secret file)
    def credential = new FileCredentialsImpl(
        CredentialsScope.GLOBAL,
        credId,
        "GCP Service Account for project: {project_id}",
        "gcp-key.json",  // file name
        jsonKeyBytes
    )

    // Add to store
    store.addCredentials(domain, credential)
    jenkins.save()

    println "SUCCESS"
}} catch (Exception e) {{
    println "ERROR:${{e.message}}"
    e.printStackTrace()
}}
"""

    def _generate_update_script(self, credential_id: str, json_content: str, project_id: str) -> str:
        """Generate Groovy script to update GCP credential"""
        escaped_json = json_content.replace("'", "\\'").replace("\n", "\\n")

        return f"""
import com.cloudbees.plugins.credentials.CredentialsProvider
import com.cloudbees.plugins.credentials.CredentialsScope
import com.cloudbees.plugins.credentials.domains.Domain
import org.jenkinsci.plugins.plaincredentials.impl.FileCredentialsImpl
import com.cloudbees.plugins.credentials.SecretBytes
import jenkins.model.Jenkins

def jenkins = Jenkins.get()
def domain = Domain.global()
def store = jenkins.getExtensionList('com.cloudbees.plugins.credentials.SystemCredentialsProvider')[0].getStore()

def credId = '{credential_id}'
def jsonKey = '''{escaped_json}'''

// Find existing credential
def existing = CredentialsProvider.lookupCredentials(
    com.cloudbees.plugins.credentials.Credentials.class,
    jenkins,
    null,
    null
).find {{ it.id == credId }}

if (existing == null) {{
    println "NOT_FOUND"
    return
}}

try {{
    // Remove old credential
    store.removeCredentials(domain, existing)

    // Create new credential with same ID
    def jsonKeyBytes = SecretBytes.fromBytes(jsonKey.getBytes('UTF-8'))

    def credential = new FileCredentialsImpl(
        CredentialsScope.GLOBAL,
        credId,
        "GCP Service Account for project: {project_id}",
        "gcp-key.json",
        jsonKeyBytes
    )

    // Add updated credential
    store.addCredentials(domain, credential)
    jenkins.save()

    println "SUCCESS"
}} catch (Exception e) {{
    println "ERROR:${{e.message}}"
    e.printStackTrace()
}}
"""

    def _generate_delete_script(self, credential_id: str) -> str:
        """Generate Groovy script to delete GCP credential"""
        return f"""
import com.cloudbees.plugins.credentials.CredentialsProvider
import com.cloudbees.plugins.credentials.domains.Domain
import jenkins.model.Jenkins

def jenkins = Jenkins.get()
def domain = Domain.global()
def store = jenkins.getExtensionList('com.cloudbees.plugins.credentials.SystemCredentialsProvider')[0].getStore()

def credId = '{credential_id}'

// Find credential
def existing = CredentialsProvider.lookupCredentials(
    com.cloudbees.plugins.credentials.Credentials.class,
    jenkins,
    null,
    null
).find {{ it.id == credId }}

if (existing == null) {{
    println "NOT_FOUND"
    return
}}

try {{
    // Remove credential
    store.removeCredentials(domain, existing)
    jenkins.save()

    println "SUCCESS"
}} catch (Exception e) {{
    println "ERROR:${{e.message}}"
    e.printStackTrace()
}}
"""

    def _generate_describe_script(self, credential_id: str, show_secret: bool) -> str:
        """Generate Groovy script to describe GCP credential"""
        return f"""
import com.cloudbees.plugins.credentials.CredentialsProvider
import org.jenkinsci.plugins.plaincredentials.impl.FileCredentialsImpl
import jenkins.model.Jenkins

def jenkins = Jenkins.get()
def credId = '{credential_id}'
def showSecret = {str(show_secret).lower()}

// Find credential
def existing = CredentialsProvider.lookupCredentials(
    com.cloudbees.plugins.credentials.Credentials.class,
    jenkins,
    null,
    null
).find {{ it.id == credId }}

if (existing == null) {{
    println "NOT_FOUND"
    return
}}

println "SUCCESS"
println "Credential: ${{credId}}"
println "Type: ${{existing.getClass().getSimpleName()}}"
println "Scope: ${{existing.getScope()}}"

if (existing instanceof FileCredentialsImpl) {{
    println "File Name: ${{existing.getFileName()}}"
    println "Description: ${{existing.getDescription() ?: '(no description)'}}"

    if (showSecret) {{
        println ""
        println "⚠️  WARNING: Displaying sensitive credential content!"
        println ""
        println "JSON Key Content:"
        println "---"
        def content = new String(existing.getSecretBytes().getPlainData(), 'UTF-8')
        println content
        println "---"
    }} else {{
        println ""
        println "Secret: [PROTECTED]"
        println ""
        def progName = "jenkee"
        println "Use --show-secret flag to display the full JSON key (use with caution!)"
    }}
}}
"""
