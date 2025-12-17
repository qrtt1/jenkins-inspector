"""Azure Storage credentials describer"""

from typing import Optional, Dict, Any
import xml.etree.ElementTree as ET

from jenkins_tools.credential_describers.base import CredentialDescriber


class AzureStorageCredentialsDescriber(CredentialDescriber):
    """Describer for AzureStorageAccount"""

    def get_credential_type(self) -> str:
        return "AzureStorageAccount"

    def get_groovy_script(self, credential_id: str) -> Optional[str]:
        # Secret retrieval not implemented for this type yet
        return None

    def parse_secret_output(self, output: str) -> Dict[str, Any]:
        return {}

    def print_details(self, cred_elem: ET.Element, secret_data: Optional[Dict[str, Any]] = None):
        print("Details:")

        storage_data = cred_elem.find("storageData")
        if storage_data is not None:
            account_name = self._get_xml_text(storage_data, "storageAccountName")
            if account_name:
                print(f"  Storage Account Name: {account_name}")

            blob_endpoint = self._get_xml_text(storage_data, "blobEndpointURL")
            if blob_endpoint:
                print(f"  Blob Endpoint URL: {blob_endpoint}")

        self._format_protected_message("Access Key")
        print()

        print("Usage in Job:")
        print("  Use with Azure Storage plugin")
        print("  For uploading/downloading artifacts to Azure Blob Storage")
        print()
