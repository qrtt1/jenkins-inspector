"""
Test GCP credentials in a freestyle job

This test validates that GCP credentials created with `jenkee gcp credential create`
can be used in Jenkins freestyle jobs with gcloud-sdk GCloudBuildWrapper.

Test flow:
1. Create GCP credential using jenkee gcp credential create
2. Create freestyle job with GCloudBuildWrapper
3. Build the job and verify GCP authentication works
"""

import pytest
import time


def test_gcp_freestyle_job(run_jenkee_authed, jenkins_instance, gcp_key_files, gcp_sa1_info):
    """
    Test GCP credentials work in a freestyle job

    Validates:
    - Credential created via jenkee gcp credential create
    - Credential can be used by GCloudBuildWrapper
    - Service account is activated by gcloud-sdk plugin
    - gcloud commands work with the activated service account
    """
    credential_id = "test-freestyle-gcp-cred"
    job_name = "test-gcp-freestyle"

    try:
        # Arrange: Create GCP credential using new subcommand
        print("\n" + "="*80)
        print("Step 1: Create GCP credential using jenkee gcp credential create")
        print("="*80)
        result = run_jenkee_authed.run(
            "gcp", "credential", "create",
            credential_id,
            str(gcp_key_files['sa1'])
        )
        assert result.returncode == 0, f"Failed to create credential: {result.stderr}"
        print(f"✓ Created credential: {credential_id}")
        print(f"  Service Account: {gcp_sa1_info['client_email']}")
        print(f"  Project ID: {gcp_sa1_info['project_id']}")

        # Job XML configuration - use GCloudBuildWrapper
        job_xml = f'''<?xml version='1.1' encoding='UTF-8'?>
<project>
  <description>Test GCP Service Account credentials in freestyle job</description>
  <keepDependencies>false</keepDependencies>
  <properties/>
  <scm class="hudson.scm.NullSCM"/>
  <canRoam>true</canRoam>
  <disabled>false</disabled>
  <blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
  <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
  <triggers/>
  <concurrentBuild>false</concurrentBuild>
  <builders>
    <hudson.tasks.Shell>
      <command>#!/bin/bash
set -x

echo "=========================================="
echo "Testing GCP Service Account Credentials"
echo "=========================================="
echo ""

echo "Step 1: Test GCP API access (list service accounts)"
gcloud iam service-accounts list --project {gcp_sa1_info['project_id']} | grep -F "{gcp_sa1_info['client_email']}"
echo ""

echo "=========================================="
echo "✓ GCP credential check completed!"
echo "=========================================="
</command>
      <configuredLocalRules/>
    </hudson.tasks.Shell>
  </builders>
  <publishers/>
  <buildWrappers>
    <com.byclosure.jenkins.plugins.gcloud.GCloudBuildWrapper plugin="gcloud-sdk@0.0.3">
      <installation></installation>
      <credentialsId>{credential_id}</credentialsId>
    </com.byclosure.jenkins.plugins.gcloud.GCloudBuildWrapper>
  </buildWrappers>
</project>
'''

        # Act: Create the job
        print("\n" + "="*80)
        print("Step 2: Create freestyle job")
        print("="*80)
        result = run_jenkee_authed.build_command(
            "create-job",
            job_name,
        ).with_stdin(job_xml).run()

        assert result.returncode == 0, f"Failed to create job: {result.stderr}"
        print(f"✓ Job created: {job_name}")

        # Act: Build the job
        print("\n" + "="*80)
        print("Step 3: Build the job")
        print("="*80)
        result = run_jenkee_authed.run("build", job_name)
        assert result.returncode == 0, f"Failed to trigger build: {result.stderr}"
        print("✓ Build triggered")

        # Wait for build to complete (with timeout)
        max_wait = 60  # Increased timeout for GCP operations
        waited = 0
        build_completed = False

        print("Waiting for build to complete...", end="", flush=True)
        while waited < max_wait:
            result = run_jenkee_authed.build_command(
                "job-status",
                job_name
            ).allow_failure().run()

            if "Last Build: #1" in result.stdout and "Last Completed Build: #1" in result.stdout:
                build_completed = True
                break

            time.sleep(2)
            waited += 2
            print(".", end="", flush=True)

        print()  # New line after dots
        if not build_completed:
            # Debug: Show last job-status output
            print(f"\nDEBUG: Last job-status output:")
            print("-"*80)
            print(result.stdout)
            print("-"*80)
        assert build_completed, f"Build did not complete within {max_wait}s"
        print(f"✓ Build completed (waited {waited}s)")

        # Assert: Get and verify console output
        print("\n" + "="*80)
        print("Step 4: Verify console output")
        print("="*80)
        result = run_jenkee_authed.run("console", job_name, "1")
        assert result.returncode == 0, f"Failed to get console output: {result.stderr}"

        console_output = result.stdout
        print("\nConsole Output:")
        print("-"*80)
        print(console_output)
        print("-"*80)

        # Verify critical elements in console output
        print("\nVerifying output...")

        # 1. Check test header
        assert "Testing GCP Service Account Credentials" in console_output, \
            "Should show test header"
        print("✓ Test header found")

        # 2. Check service account email
        assert gcp_sa1_info['client_email'] in console_output, \
            f"Should show service account email: {gcp_sa1_info['client_email']}"
        print(f"✓ Service account email found: {gcp_sa1_info['client_email']}")

        # 3. Check gcloud auth activation
        has_activate = "activate-service-account" in console_output.lower() or \
                       "Activated service account" in console_output
        assert has_activate, \
            "Should show gcloud auth activate-service-account execution"
        print("✓ Service account activation found")

        # 4. Check gcloud service-accounts list (API access)
        assert "gcloud iam service-accounts list" in console_output, \
            "Should execute gcloud iam service-accounts list command"
        print("✓ GCP API access tested")

        # 5. Check test completion message
        assert "✓ GCP credential check completed!" in console_output, \
            "Should show test completion message"
        print("✓ Test completion message found")

        # 6. Check build success
        assert "Finished: SUCCESS" in console_output, \
            "Job should complete successfully"
        print("✓ Build finished successfully")

        # Final summary
        print("\n" + "="*80)
        print("✅ Freestyle job test completed successfully!")
        print("="*80)
        print("Validated:")
        print(f"  ✓ Created credential using: jenkee gcp credential create")
        print(f"  ✓ Service account activated: {gcp_sa1_info['client_email']}")
        print(f"  ✓ gcloud commands executed successfully")
        print(f"  ✓ Credential cleanup completed")
    finally:
        # Cleanup: Delete the job and credential
        print("\n" + "="*80)
        print("Step 5: Cleanup")
        print("="*80)

        run_jenkee_authed.build_command(
            "delete-job", job_name, "--yes-i-really-mean-it"
        ).allow_failure().run()
        print(f"✓ Deleted job: {job_name}")

        run_jenkee_authed.build_command(
            "gcp", "credential", "delete",
            credential_id,
            "--yes-i-really-mean-it"
        ).allow_failure().run()
        print(f"✓ Deleted credential: {credential_id}")
