"""GCP credentials describer"""

from typing import Optional, Dict, Any
import xml.etree.ElementTree as ET

from jenkins_tools.credential_describers.base import CredentialDescriber


class GCPCredentialsDescriber(CredentialDescriber):
    """Describer for GoogleRobotPrivateKeyCredentials (GCP Service Account)"""

    def get_credential_type(self) -> str:
        return "GoogleRobotPrivateKeyCredentials"

    def get_groovy_script(self, credential_id: str) -> Optional[str]:
        return f"""
import com.google.jenkins.plugins.credentials.oauth.*

def credId = '{credential_id}'
def cred = null

def allCreds = com.cloudbees.plugins.credentials.CredentialsProvider.lookupCredentials(
    com.cloudbees.plugins.credentials.Credentials.class,
    jenkins.model.Jenkins.instance
)

allCreds.each {{ c ->
    if (c.id == credId) {{
        cred = c
    }}
}}

if (cred != null && cred instanceof GoogleRobotPrivateKeyCredentials) {{
    println "PROJECT_ID:${{cred.projectId}}"
    def config = cred.serviceAccountConfig
    if (config != null) {{
        def secretKey = config.secretJsonKey
        if (secretKey != null) {{
            def keyContent = new String(secretKey.plainData)
            println "SERVICE_ACCOUNT_KEY_START"
            println keyContent
            println "SERVICE_ACCOUNT_KEY_END"
        }}
    }}
}}
"""

    def parse_secret_output(self, output: str) -> Dict[str, Any]:
        lines = output.strip().split("\n")
        secret_data = {}

        i = 0
        while i < len(lines):
            line = lines[i]
            if line.startswith("PROJECT_ID:"):
                secret_data["project_id"] = line.split(":", 1)[1]
            elif line == "SERVICE_ACCOUNT_KEY_START":
                key_lines = []
                i += 1
                while i < len(lines) and lines[i] != "SERVICE_ACCOUNT_KEY_END":
                    key_lines.append(lines[i])
                    i += 1
                secret_data["service_account_key"] = "\n".join(key_lines)
            i += 1

        return secret_data

    def print_details(self, cred_elem: ET.Element, secret_data: Optional[Dict[str, Any]] = None):
        print("Details:")

        project_id = self._get_xml_text(cred_elem, "projectId")
        if project_id:
            print(f"  Project ID: {project_id}")

        # Print service account key if available
        if secret_data and "service_account_key" in secret_data:
            self._format_secret(secret_data["service_account_key"], "Service Account Key")
        else:
            self._format_protected_message("Service Account Key")
        print()

        print("Usage in Job:")
        print("  Use with Google Cloud Build Wrapper")
        print("  Or use 'Google Service Account from private key' credential binding")
        print()
