"""Base class for credential describers"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import xml.etree.ElementTree as ET


class CredentialDescriber(ABC):
    """Abstract base class for credential type describers"""

    @abstractmethod
    def get_credential_type(self) -> str:
        """
        Get the credential type this describer handles

        Returns:
            Credential type name (e.g., "FileCredentialsImpl")
        """
        pass

    @abstractmethod
    def get_groovy_script(self, credential_id: str) -> Optional[str]:
        """
        Generate Groovy script to retrieve secret content

        Args:
            credential_id: The credential ID

        Returns:
            Groovy script string, or None if secret retrieval is not supported
        """
        pass

    @abstractmethod
    def parse_secret_output(self, output: str) -> Dict[str, Any]:
        """
        Parse the Groovy script output to extract secret data

        Args:
            output: Output from Groovy script execution

        Returns:
            Dictionary containing parsed secret data
        """
        pass

    @abstractmethod
    def print_details(self, cred_elem: ET.Element, secret_data: Optional[Dict[str, Any]] = None):
        """
        Print credential-specific details

        Args:
            cred_elem: XML element containing credential metadata
            secret_data: Optional dictionary containing secret data from Groovy script
        """
        pass

    def _get_xml_text(self, elem: ET.Element, path: str, default: str = "") -> str:
        """
        Helper method to safely get text from XML element

        Args:
            elem: XML element to search in
            path: Path to the target element
            default: Default value if element not found

        Returns:
            Text content or default value
        """
        target = elem.find(path)
        return target.text if target is not None and target.text else default

    def _format_secret(self, secret_content: str, label: str = "Content") -> None:
        """
        Helper method to format and print secret content with separator

        Args:
            secret_content: The secret content to print
            label: Label to display before the content
        """
        print(f"  {label}:")
        print("=" * 60)
        print(secret_content)
        print("=" * 60)

    def _format_protected_message(self, label: str = "Content") -> None:
        """
        Helper method to print protected message

        Args:
            label: Label for the protected field
        """
        print(f"  {label}: [PROTECTED - Use --show-secret to display]")
