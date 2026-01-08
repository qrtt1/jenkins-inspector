"""Job status command"""

import sys

from jenkins_tools.core import Command, JenkinsConfig, JenkinsCLI


class JobStatusCommand(Command):
    """Display job status including builds and triggers"""

    def __init__(self, args):
        """
        Initialize with command line arguments

        Args:
            args: List of command arguments (sys.argv[2:])
        """
        self.args = args

    def execute(self) -> int:
        """Execute job-status command"""
        config = JenkinsConfig()

        # Check if credentials are configured
        if not config.is_configured():
            print("Error: Jenkins credentials not configured.", file=sys.stderr)
            print(f"Run 'jks auth' to configure credentials.", file=sys.stderr)
            return 1

        # Parse arguments
        if not self.args:
            print("Error: Missing job name", file=sys.stderr)
            print("Usage: jks job-status <job-name>", file=sys.stderr)
            return 1

        job_name = self.args[0]

        # Use groovy script to get job status
        cli = JenkinsCLI(config)
        groovy_script = f"""
def job = hudson.model.Hudson.instance.getItemByFullName('{job_name}')

if (!job) {{
    println "ERROR: Job not found"
    return
}}

// Basic info
println "=== Job: " + job.fullName + " ==="
println ""
println "Status: " + (job.disabled ? "DISABLED" : "ENABLED")
println "Buildable: " + job.buildable
println ""

// Health report
if (job.hasProperty('buildHealth') && job.buildHealth && job.buildHealth.score != null) {{
    def health = job.buildHealth
    println "=== Health ==="
    println "Score: " + health.score + "%"
    println "Description: " + health.description
    println ""
}}

// Last builds (permalinks)
println "=== Last Builds ==="
if (job.lastBuild) {{
    println "Last Build: #" + job.lastBuild.number
}}
if (job.lastStableBuild) {{
    println "Last Stable Build: #" + job.lastStableBuild.number
}}
if (job.lastSuccessfulBuild) {{
    println "Last Successful Build: #" + job.lastSuccessfulBuild.number
}}
if (job.lastFailedBuild) {{
    println "Last Failed Build: #" + job.lastFailedBuild.number
}}
if (job.lastUnsuccessfulBuild) {{
    println "Last Unsuccessful Build: #" + job.lastUnsuccessfulBuild.number
}}
if (job.lastCompletedBuild) {{
    println "Last Completed Build: #" + job.lastCompletedBuild.number
}}
println ""

// Downstream projects (this job triggers)
println "=== Downstream Projects ==="
if (job.hasProperty('downstreamProjects') && job.downstreamProjects && job.downstreamProjects.size() > 0) {{
    job.downstreamProjects.each {{ downstream ->
        println "  - " + downstream.fullName
    }}
}} else {{
    println "  (none)"
}}
println ""

// Upstream projects (triggered by)
println "=== Upstream Projects ==="
if (job.hasProperty('upstreamProjects') && job.upstreamProjects && job.upstreamProjects.size() > 0) {{
    job.upstreamProjects.each {{ upstream ->
        println "  - " + upstream.fullName
    }}
}} else {{
    println "  (none)"
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
                print(f"Error: Failed to get status for job '{job_name}'", file=sys.stderr)
                return 1
        else:
            print(f"Error: Failed to get status for job '{job_name}'", file=sys.stderr)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            return 1
