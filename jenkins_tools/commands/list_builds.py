"""List builds command"""

import sys

from jenkins_tools.core import Command, JenkinsConfig, JenkinsCLI


class ListBuildsCommand(Command):
    """List build history for a Jenkins job"""

    def __init__(self, args):
        """
        Initialize with command line arguments

        Args:
            args: List of command arguments (sys.argv[2:])
        """
        self.args = args

    def execute(self) -> int:
        """Execute list-builds command"""
        config = JenkinsConfig()

        # Check if credentials are configured
        if not config.is_configured():
            print("Error: Jenkins credentials not configured.", file=sys.stderr)
            print(f"Run 'jks auth' to configure credentials.", file=sys.stderr)
            return 1

        # Parse arguments
        if not self.args:
            print("Error: Missing job name", file=sys.stderr)
            print("Usage: jks list-builds <job-name>", file=sys.stderr)
            return 1

        job_name = self.args[0]

        # Use groovy script to list builds
        cli = JenkinsCLI(config)
        groovy_script = f"""
def job = hudson.model.Hudson.instance.getItemByFullName('{job_name}')
if (job) {{
  job.builds.each {{ build ->
    def result = build.result ? build.result.toString() : 'BUILDING'
    def timestamp = build.time.format('yyyy-MM-dd HH:mm:ss')
    def duration = build.duration / 1000  // 轉換為秒
    println "#${{build.number}} ${{result}} ${{timestamp}} ${{duration}}s"
  }}
}} else {{
  println "ERROR: Job not found"
}}
"""

        result = cli.run("groovy", "=", stdin_input=groovy_script)

        if result.returncode == 0:
            output = result.stdout.strip()
            if output and not output.startswith("ERROR:"):
                print(output)
                return 0
            elif output.startswith("ERROR:"):
                print(f"Error: Job '{job_name}' not found", file=sys.stderr)
                return 1
            else:
                print(f"No builds found for job '{job_name}'")
                return 0
        else:
            print(f"Error: Failed to list builds for job '{job_name}'", file=sys.stderr)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            return 1
