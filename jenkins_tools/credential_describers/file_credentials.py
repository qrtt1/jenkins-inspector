"""File credentials describer"""

from typing import Optional, Dict, Any
import xml.etree.ElementTree as ET

from jenkins_tools.credential_describers.base import CredentialDescriber


class FileCredentialsDescriber(CredentialDescriber):
    """Describer for FileCredentialsImpl (Secret file)"""

    def get_credential_type(self) -> str:
        return "FileCredentialsImpl"

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

if (cred != null && cred instanceof FileCredentialsImpl) {{
    def content = new String(cred.secretBytes.plainData)
    println "FILE_CONTENT_START"
    println content
    println "FILE_CONTENT_END"
}}
"""

    def parse_secret_output(self, output: str) -> Dict[str, Any]:
        lines = output.strip().split("\n")
        secret_data = {}

        i = 0
        while i < len(lines):
            line = lines[i]
            if line == "FILE_CONTENT_START":
                content_lines = []
                i += 1
                while i < len(lines) and lines[i] != "FILE_CONTENT_END":
                    content_lines.append(lines[i])
                    i += 1
                secret_data["file_content"] = "\n".join(content_lines)
            i += 1

        return secret_data

    def print_details(self, cred_elem: ET.Element, secret_data: Optional[Dict[str, Any]] = None):
        print("Details:")

        filename = self._get_xml_text(cred_elem, "fileName")
        if filename:
            print(f"  File Name: {filename}")

        # Print file content if available
        if secret_data and "file_content" in secret_data:
            self._format_secret(secret_data["file_content"], "Content")
        else:
            self._format_protected_message("Content")
        print()

        print("Usage in Job:")
        print("  Use 'Secret file' credential binding in job configuration")
        print("  The file will be available at a temporary path during build")
        print()
