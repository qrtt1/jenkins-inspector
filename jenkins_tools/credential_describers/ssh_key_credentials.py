"""SSH key credentials describer"""

from typing import Optional, Dict, Any
import xml.etree.ElementTree as ET

from jenkins_tools.credential_describers.base import CredentialDescriber


class SSHKeyCredentialsDescriber(CredentialDescriber):
    """Describer for BasicSSHUserPrivateKey (SSH private key)"""

    def get_credential_type(self) -> str:
        return "BasicSSHUserPrivateKey"

    def get_groovy_script(self, credential_id: str) -> Optional[str]:
        return f"""
import com.cloudbees.jenkins.plugins.sshcredentials.impl.*

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

if (cred != null && cred instanceof BasicSSHUserPrivateKey) {{
    println "USERNAME:${{cred.username}}"
    def keyContent = cred.privateKey
    println "PRIVATE_KEY_START"
    println keyContent
    println "PRIVATE_KEY_END"
}}
"""

    def parse_secret_output(self, output: str) -> Dict[str, Any]:
        lines = output.strip().split("\n")
        secret_data = {}

        i = 0
        while i < len(lines):
            line = lines[i]
            if line.startswith("USERNAME:"):
                secret_data["username"] = line.split(":", 1)[1]
            elif line == "PRIVATE_KEY_START":
                key_lines = []
                i += 1
                while i < len(lines) and lines[i] != "PRIVATE_KEY_END":
                    key_lines.append(lines[i])
                    i += 1
                secret_data["private_key"] = "\n".join(key_lines)
            i += 1

        return secret_data

    def print_details(self, cred_elem: ET.Element, secret_data: Optional[Dict[str, Any]] = None):
        print("Details:")

        username = self._get_xml_text(cred_elem, "username")
        if username:
            print(f"  Username: {username}")

        private_key_source = cred_elem.find("privateKeySource")
        if private_key_source is not None:
            key_type = private_key_source.get("class", "").split(".")[-1]
            print(f"  Private Key Source: {key_type}")

        # Print private key if available
        if secret_data and "private_key" in secret_data:
            self._format_secret(secret_data["private_key"], "Private Key")
        else:
            self._format_protected_message("Private Key")
        print()

        print("Usage in Job:")
        print("  Use 'SSH User Private Key' credential binding")
        print("  Or use in SSH-based SCM configurations")
        print()
