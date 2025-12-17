"""String credentials describer"""

from typing import Optional, Dict, Any
import xml.etree.ElementTree as ET

from jenkins_tools.credential_describers.base import CredentialDescriber


class StringCredentialsDescriber(CredentialDescriber):
    """Describer for StringCredentialsImpl (Secret text)"""

    def get_credential_type(self) -> str:
        return "StringCredentialsImpl"

    def get_groovy_script(self, credential_id: str) -> Optional[str]:
        return f"""
import org.jenkinsci.plugins.plaincredentials.impl.*

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

if (cred != null && cred instanceof StringCredentialsImpl) {{
    println "SECRET:${{cred.secret}}"
}}
"""

    def parse_secret_output(self, output: str) -> Dict[str, Any]:
        lines = output.strip().split("\n")
        secret_data = {}

        for line in lines:
            if line.startswith("SECRET:"):
                secret_data["secret"] = line.split(":", 1)[1]

        return secret_data

    def print_details(self, cred_elem: ET.Element, secret_data: Optional[Dict[str, Any]] = None):
        print("Details:")

        # Print secret if available
        if secret_data and "secret" in secret_data:
            print(f"  Secret Text: {secret_data['secret']}")
        else:
            self._format_protected_message("Secret Text")
        print()

        print("Usage in Job:")
        print("  Use 'Secret text' credential binding")
        print("  The secret will be available as an environment variable")
        print()
