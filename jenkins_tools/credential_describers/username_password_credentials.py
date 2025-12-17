"""Username/Password credentials describer"""

from typing import Optional, Dict, Any
import xml.etree.ElementTree as ET

from jenkins_tools.credential_describers.base import CredentialDescriber


class UsernamePasswordCredentialsDescriber(CredentialDescriber):
    """Describer for UsernamePasswordCredentialsImpl"""

    def get_credential_type(self) -> str:
        return "UsernamePasswordCredentialsImpl"

    def get_groovy_script(self, credential_id: str) -> Optional[str]:
        return f"""
import com.cloudbees.plugins.credentials.impl.*

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

if (cred != null && cred instanceof UsernamePasswordCredentialsImpl) {{
    println "USERNAME:${{cred.username}}"
    println "PASSWORD:${{cred.password}}"
}}
"""

    def parse_secret_output(self, output: str) -> Dict[str, Any]:
        lines = output.strip().split("\n")
        secret_data = {}

        for line in lines:
            if line.startswith("USERNAME:"):
                secret_data["username"] = line.split(":", 1)[1]
            elif line.startswith("PASSWORD:"):
                secret_data["password"] = line.split(":", 1)[1]

        return secret_data

    def print_details(self, cred_elem: ET.Element, secret_data: Optional[Dict[str, Any]] = None):
        print("Details:")

        username = self._get_xml_text(cred_elem, "username")
        if username:
            print(f"  Username: {username}")

        # Print password if available
        if secret_data and "password" in secret_data:
            print(f"  Password: {secret_data['password']}")
        else:
            self._format_protected_message("Password")
        print()

        print("Usage in Job:")
        print("  Use 'Username and password' credential binding")
        print("  Separate variables for username and password can be specified")
        print()
