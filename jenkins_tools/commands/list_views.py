"""List views command"""

import sys

from jenkins_tools.core import Command, JenkinsConfig, JenkinsCLI


class ListViewsCommand(Command):
    """List all Jenkins views"""

    def execute(self) -> int:
        """Execute list-views command"""
        config = JenkinsConfig()

        # Check if credentials are configured
        if not config.is_configured():
            print("Error: Jenkins credentials not configured.", file=sys.stderr)
            print(f"Run 'jks auth' to configure credentials.", file=sys.stderr)
            return 1

        # Use groovy script to list views
        cli = JenkinsCLI(config)
        groovy_script = r"println hudson.model.Hudson.instance.views*.name.sort().join('\n')"

        result = cli.run("groovy", "=", stdin_input=groovy_script)

        if result.returncode == 0:
            print(result.stdout.strip())
            return 0
        else:
            print("Error: Failed to list views", file=sys.stderr)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            return 1
