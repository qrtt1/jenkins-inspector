"""BrowserStack credentials describer"""

from typing import Optional, Dict, Any
import xml.etree.ElementTree as ET

from jenkins_tools.credential_describers.base import CredentialDescriber


class BrowserStackCredentialsDescriber(CredentialDescriber):
    """Describer for BrowserStackCredentials"""

    def get_credential_type(self) -> str:
        return "BrowserStackCredentials"

    def get_groovy_script(self, credential_id: str) -> Optional[str]:
        # Secret retrieval not implemented for this type yet
        return None

    def parse_secret_output(self, output: str) -> Dict[str, Any]:
        return {}

    def print_details(self, cred_elem: ET.Element, secret_data: Optional[Dict[str, Any]] = None):
        print("Details:")

        username = self._get_xml_text(cred_elem, "username")
        if username:
            print(f"  Username: {username}")

        self._format_protected_message("Access Key")
        print()

        print("Usage in Job:")
        print("  Use with BrowserStack plugin for automated testing")
        print()
