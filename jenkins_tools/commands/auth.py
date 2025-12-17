"""Authentication command"""

import sys
from pathlib import Path

from jenkins_tools.core import Command, JenkinsConfig, JenkinsCLI


class AuthCommand(Command):
    """Verify Jenkins authentication"""

    def execute(self) -> int:
        """Execute auth command - verify credentials by running whoami"""
        config = JenkinsConfig()

        # Check if credentials are configured
        if not config.is_configured():
            print("Error: Jenkins credentials not configured.", file=sys.stderr)
            print("", file=sys.stderr)
            print(f"Please create a .env file at: {config.env_path}", file=sys.stderr)
            if config.legacy_env_path.exists() and not config.env_path.exists():
                print("", file=sys.stderr)
                print(
                    f"Detected legacy config at: {config.legacy_env_path}",
                    file=sys.stderr,
                )
                print(
                    f"Please move it to: {config.env_path}",
                    file=sys.stderr,
                )
            print("", file=sys.stderr)
            print("Content:", file=sys.stderr)
            print("  JENKINS_URL=http://your-jenkins-server:8080/", file=sys.stderr)
            print("  JENKINS_USER_ID=your_email@example.com", file=sys.stderr)
            print("  JENKINS_API_TOKEN=your_api_token", file=sys.stderr)
            print("", file=sys.stderr)
            print("You can get your API token from:", file=sys.stderr)
            print("  Jenkins > User > Configure > API Token", file=sys.stderr)
            return 1

        # Run who-am-i to verify authentication
        cli = JenkinsCLI(config)
        print("Verifying authentication...")

        result = cli.run("who-am-i")

        if result.returncode == 0:
            output = (result.stdout or "").strip()
            lines = [line for line in output.splitlines() if line.strip()]
            if lines:
                first_line = lines[0]
                if first_line.startswith("Authenticated as:"):
                    print(f"✓ {first_line}")
                    if len(lines) > 1:
                        print("\n".join(lines[1:]))
                else:
                    print(f"✓ Authenticated as: {first_line}")
                    if len(lines) > 1:
                        print("\n".join(lines[1:]))
            else:
                print("✓ Authentication successful")
            return 0
        else:
            print("✗ Authentication failed", file=sys.stderr)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            return 1
