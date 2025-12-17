"""GitLab API token credentials describer"""

from typing import Optional, Dict, Any
import xml.etree.ElementTree as ET

from jenkins_tools.credential_describers.base import CredentialDescriber


class GitLabTokenCredentialsDescriber(CredentialDescriber):
    """Describer for GitLabApiTokenImpl"""

    def get_credential_type(self) -> str:
        return "GitLabApiTokenImpl"

    def get_groovy_script(self, credential_id: str) -> Optional[str]:
        # Secret retrieval not implemented for this type yet
        return None

    def parse_secret_output(self, output: str) -> Dict[str, Any]:
        return {}

    def print_details(self, cred_elem: ET.Element, secret_data: Optional[Dict[str, Any]] = None):
        print("Details:")
        self._format_protected_message("API Token")
        print()

        print("Usage in Job:")
        print("  Use with GitLab plugin for API authentication")
        print("  Typically used for merge request status updates")
        print()
