"""Credential describers for different credential types"""

from jenkins_tools.credential_describers.base import CredentialDescriber
from jenkins_tools.credential_describers.file_credentials import FileCredentialsDescriber
from jenkins_tools.credential_describers.ssh_key_credentials import SSHKeyCredentialsDescriber
from jenkins_tools.credential_describers.username_password_credentials import (
    UsernamePasswordCredentialsDescriber,
)
from jenkins_tools.credential_describers.string_credentials import StringCredentialsDescriber
from jenkins_tools.credential_describers.gcp_credentials import GCPCredentialsDescriber
from jenkins_tools.credential_describers.azure_storage_credentials import (
    AzureStorageCredentialsDescriber,
)
from jenkins_tools.credential_describers.azure_credentials import AzureCredentialsDescriber
from jenkins_tools.credential_describers.browserstack_credentials import (
    BrowserStackCredentialsDescriber,
)
from jenkins_tools.credential_describers.gitlab_token_credentials import (
    GitLabTokenCredentialsDescriber,
)

# Registry of credential describers by type
CREDENTIAL_DESCRIBERS = {
    "FileCredentialsImpl": FileCredentialsDescriber(),
    "BasicSSHUserPrivateKey": SSHKeyCredentialsDescriber(),
    "UsernamePasswordCredentialsImpl": UsernamePasswordCredentialsDescriber(),
    "StringCredentialsImpl": StringCredentialsDescriber(),
    "GoogleRobotPrivateKeyCredentials": GCPCredentialsDescriber(),
    "AzureStorageAccount": AzureStorageCredentialsDescriber(),
    "AzureCredentials": AzureCredentialsDescriber(),
    "BrowserStackCredentials": BrowserStackCredentialsDescriber(),
    "GitLabApiTokenImpl": GitLabTokenCredentialsDescriber(),
}

__all__ = [
    "CredentialDescriber",
    "CREDENTIAL_DESCRIBERS",
]
