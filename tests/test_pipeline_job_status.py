"""
Test job-status command with Pipeline jobs

This test validates that `jenkee job-status` works correctly with Pipeline jobs
(WorkflowJob), which don't have downstreamProjects/upstreamProjects properties.

Test flow:
1. Create a simple Pipeline job
2. Run job-status command
3. Verify no errors occur
4. Verify output contains expected information
"""

import pytest


def test_pipeline_job_status(run_jenkee_authed, jenkins_instance):
    """
    Test job-status command with Pipeline job

    Validates:
    - Pipeline job can be queried without downstreamProjects error
    - Status output contains expected sections
    - Upstream/Downstream sections show "(none)" for Pipeline jobs
    """
    job_name = "test-pipeline-job"

    try:
        # Arrange: Create a simple Pipeline job
        print("\n" + "="*80)
        print("Step 1: Create Pipeline job")
        print("="*80)

        # Pipeline job XML configuration
        job_xml = '''<?xml version='1.1' encoding='UTF-8'?>
<flow-definition plugin="workflow-job">
  <description>Test Pipeline job for job-status command</description>
  <keepDependencies>false</keepDependencies>
  <properties/>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition" plugin="workflow-cps">
    <script>
pipeline {
    agent any
    stages {
        stage('Test') {
            steps {
                echo 'Hello from Pipeline'
            }
        }
    }
}
    </script>
    <sandbox>true</sandbox>
  </definition>
  <triggers/>
  <disabled>false</disabled>
</flow-definition>
'''

        result = run_jenkee_authed.build_command(
            "create-job",
            job_name,
        ).with_stdin(job_xml).run()

        assert result.returncode == 0, f"Failed to create job: {result.stderr}"
        print(f"✓ Pipeline job created: {job_name}")

        # Act: Run job-status command
        print("\n" + "="*80)
        print("Step 2: Run job-status command")
        print("="*80)
        result = run_jenkee_authed.run("job-status", job_name)

        # Assert: Command should succeed
        assert result.returncode == 0, f"job-status failed: {result.stderr}"
        print("✓ job-status command succeeded")

        # Assert: Verify output content
        print("\n" + "="*80)
        print("Step 3: Verify output")
        print("="*80)
        output = result.stdout
        print("\nJob Status Output:")
        print("-"*80)
        print(output)
        print("-"*80)

        # Check for expected sections
        assert f"=== Job: {job_name} ===" in output, \
            "Should show job name header"
        print("✓ Job header found")

        assert "Status:" in output, \
            "Should show status section"
        print("✓ Status section found")

        assert "=== Downstream Projects ===" in output, \
            "Should show Downstream Projects section"
        print("✓ Downstream Projects section found")

        assert "=== Upstream Projects ===" in output, \
            "Should show Upstream Projects section"
        print("✓ Upstream Projects section found")

        # For Pipeline jobs, upstream/downstream should show "(none)"
        # since these properties don't exist on WorkflowJob
        downstream_section_found = False
        upstream_section_found = False
        lines = output.split('\n')
        for i, line in enumerate(lines):
            if "=== Downstream Projects ===" in line:
                downstream_section_found = True
                # Check next non-empty line
                for j in range(i+1, len(lines)):
                    if lines[j].strip():
                        assert "(none)" in lines[j], \
                            "Downstream Projects should show '(none)' for Pipeline jobs"
                        print("✓ Downstream Projects shows '(none)' correctly")
                        break
            if "=== Upstream Projects ===" in line:
                upstream_section_found = True
                # Check next non-empty line
                for j in range(i+1, len(lines)):
                    if lines[j].strip():
                        assert "(none)" in lines[j], \
                            "Upstream Projects should show '(none)' for Pipeline jobs"
                        print("✓ Upstream Projects shows '(none)' correctly")
                        break

        assert downstream_section_found and upstream_section_found, \
            "Both Upstream and Downstream sections should be present"

        # Most importantly: verify no MissingPropertyException error
        assert "MissingPropertyException" not in result.stderr, \
            "Should not have MissingPropertyException error"
        assert "No such property: downstreamProjects" not in result.stderr, \
            "Should not have downstreamProjects error"
        print("✓ No MissingPropertyException errors")

        # Final summary
        print("\n" + "="*80)
        print("✅ Pipeline job-status test completed successfully!")
        print("="*80)
        print("Validated:")
        print(f"  ✓ Pipeline job created: {job_name}")
        print(f"  ✓ job-status command executed without errors")
        print(f"  ✓ No MissingPropertyException for downstreamProjects")
        print(f"  ✓ Output shows proper sections with '(none)' for upstream/downstream")

    finally:
        # Cleanup: Delete the job
        print("\n" + "="*80)
        print("Step 4: Cleanup")
        print("="*80)

        run_jenkee_authed.build_command(
            "delete-job", job_name, "--yes-i-really-mean-it"
        ).allow_failure().run()
        print(f"✓ Deleted job: {job_name}")
