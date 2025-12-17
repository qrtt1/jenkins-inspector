"""Azure credentials describer"""

from typing import Optional, Dict, Any
import xml.etree.ElementTree as ET

from jenkins_tools.credential_describers.base import CredentialDescriber


class AzureCredentialsDescriber(CredentialDescriber):
    """Describer for AzureCredentials (Service Principal)"""

    def get_credential_type(self) -> str:
        return "AzureCredentials"

    def get_groovy_script(self, credential_id: str) -> Optional[str]:
        # Secret retrieval not implemented for this type yet
        return None

    def parse_secret_output(self, output: str) -> Dict[str, Any]:
        return {}

    def print_details(self, cred_elem: ET.Element, secret_data: Optional[Dict[str, Any]] = None):
        print("Details:")

        subscription_id = self._get_xml_text(cred_elem, "subscriptionId")
        if subscription_id:
            print(f"  Subscription ID: {subscription_id}")

        client_id = self._get_xml_text(cred_elem, "clientId")
        if client_id:
            print(f"  Client ID: {client_id}")

        tenant = self._get_xml_text(cred_elem, "tenant")
        if tenant:
            print(f"  Tenant: {tenant}")

        self._format_protected_message("Client Secret")
        print()

        print("Usage in Job:")
        print("  Use with Azure plugins for service principal authentication")
        print()
