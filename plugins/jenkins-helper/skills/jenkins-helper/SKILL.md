---
name: jenkins-helper
description: "Manage and interact with Jenkins using the jenkee CLI tool. TRIGGERING RULES: (A) MUST trigger when user mentions 'jenkins' or 'jenkee' with any Jenkins-related task. (B) MUST trigger when 'jks' appears with Jenkins context keywords like: job, build, console, credential, view, pipeline, or groovy. (C) When user only mentions 'jks' without clear context, ask for clarification before triggering. CAPABILITIES: (1) Finding jobs by name or pattern, (2) Checking job status, build history, or console logs, (3) Modifying job configurations like branch changes, (4) Managing credentials and domains, (5) Comparing job configurations, (6) Switching between multiple Jenkins sites via profiles, (7) Any other Jenkins-related operations. This skill uses the jenkee command-line tool (also aliased as jks)."
---

# Jenkins Helper

## Overview

This skill enables interaction with Jenkins through the `jenkee` CLI tool (also aliased as `jks`), providing capabilities for job management, build monitoring, credential handling, configuration updates, and switching between multiple Jenkins sites.

**Command aliases:**
- `jenkee` - Primary command name
- `jks` - Short alias (identical functionality)

**Note:** This skill does NOT install or configure jenkee for the user. It only helps use jenkee once it's installed and configured.

## Setup

### Installation (User Responsibility)

If jenkee is not installed, inform the user they need to install it themselves:

```bash
# Using pip
pip install jenkee

# Using pipx (recommended for CLI tools)
pipx install jenkee
```

**Installation details:**
- PyPI package: `jenkee`
- GitHub repository: https://github.com/qrtt1/jenkins-inspector
- Documentation: `jenkee help` (all commands) and `jenkee help <command>` (per-command syntax, options, and examples) after installation

### Authentication Setup (User Responsibility)

If `jenkee auth` fails, inform the user they need to configure authentication themselves:

1. Create configuration directory:
```bash
mkdir -p ~/.jenkins-inspector
```

2. Create `.env` file with Jenkins credentials:
```bash
cat > ~/.jenkins-inspector/.env << EOF
JENKINS_URL=http://your-jenkins-server:8080/
JENKINS_USER_ID=your_email@example.com
JENKINS_API_TOKEN=your_api_token
EOF
```

3. Get API Token from Jenkins:
   - Log into Jenkins web interface
   - Go to: User → Configure → API Token
   - Generate and copy the token

**Important:** You should NOT create or modify these files for the user. Only provide the instructions.

### Multiple Jenkins Sites (Profiles)

jenkee supports named connection profiles for users who work with more than one Jenkins server. This is user-configured (each profile is its own `.env`-style file); the skill only helps *use* profiles that already exist.

```bash
# List all configured profiles, showing which one is active
jenkee profile list

# Switch the persistent active profile
jenkee profile use <name>
jenkee profile use --default

# Show which profile is active and where its config came from
jenkee profile current
```

A profile can also be selected just for one invocation without changing the persistent state:

```bash
jenkee --profile <name> <command>
# or
JENKEE_PROFILE=<name> jenkee <command>
```

If the user asks to create a new profile, give them the instructions (do not create files for them):

```bash
mkdir -p ~/.jenkins-inspector/profiles
cat > ~/.jenkins-inspector/profiles/<name>.env << EOF
JENKINS_URL=http://other-jenkins-server:8080/
JENKINS_USER_ID=your_email@example.com
JENKINS_API_TOKEN=your_api_token
EOF
```

**Why this matters for safety:** when profiles are in use, `jenkee` always prints `Active profile: <name> (<url>)` before running, and again before any destructive confirmation. Read that line rather than assuming which Jenkins site a command targets — see the Safety Protocol below.

## Verification

Before using any jenkee commands:

1. **Verify jenkee installation:**

```bash
command -v jenkee
```

If not installed, provide installation instructions above and stop.

2. **Verify authentication:**

```bash
jenkee auth
```

If authentication fails, provide authentication setup instructions above and stop.

3. **Check which site is active (if profiles may be in use):**

```bash
jenkee profile current
```

If this reports a profile you didn't expect, confirm with the user which Jenkins site they mean before proceeding — do not silently assume the default.

4. **Confirm the current command surface:**

```bash
jenkee help
```

Command names and flags can change between versions. `jenkee help` always reflects the version actually installed, so treat its output as authoritative over anything memorized here. Run `jenkee help <command>` for the full syntax, options, and worked examples of any specific command before using it for the first time in a session.

## Core Workflows

### Finding Jobs

To find jobs by name pattern:

```bash
# List all views first
jenkee list-views

# List jobs in a specific view
jenkee list-jobs <view-name>

# To search across all jobs for a pattern like "rich"
jenkee list-jobs --all | grep -i rich
```

### Checking Job Status

To check job status and recent builds:

```bash
# Get job status and trigger relationships
jenkee job-status <job-name>

# List build history
jenkee list-builds <job-name>

# View console output of latest build
jenkee console <job-name>

# View specific build console
jenkee console <job-name> <build-number>
```

### Triggering and Stopping Builds

```bash
# Trigger a build (see `jenkee help build` for parameters, sync/follow flags)
jenkee build <job-name>

# Stop running builds for one or more jobs
jenkee stop-builds <job-name> [job-name ...]
```

### Modifying Job Configuration

To modify job settings like changing the branch:

```bash
# 1. ALWAYS get the LATEST job configuration first
jenkee get-job <job-name> > job-config.xml

# 2. Edit the XML file to change settings
# For branch changes, look for <branches> section in XML

# 3. Update the job with modified configuration
jenkee update-job <job-name> < job-config.xml
```

**CRITICAL: Always fetch fresh configuration before updating**

Never reuse old local XML files. Always run `jenkee get-job` immediately before making changes to:
- Avoid overwriting manual changes made by others via Jenkins UI
- Prevent race conditions when multiple people modify the same job
- Ensure your changes are based on the current state

**When modifying XML:**
- For Git branch changes, find the `<hudson.plugins.git.BranchSpec>` section
- Update the `<name>` field to the desired branch (e.g., `*/foobar` or `foobar`)
- Preserve all XML structure and formatting

### Creating Jobs and Organizing Views

```bash
# Create a new job from an XML configuration file
jenkee create-job <job-name> < config.xml

# Add existing jobs to a view
jenkee add-job-to-view <view-name> <job-name> [job-name ...]
```

### Managing Credentials and Domains

```bash
# List all credential domains
jenkee domain list

# Create a new domain (requires confirmation)
jenkee domain create <name> --description="..." --yes-i-really-mean-it

# List all credentials
jenkee list-credentials

# List credentials in specific domain
jenkee list-credentials <domain-name>

# View credential details
jenkee describe-credentials <credential-id>

# Create GCP credential
jenkee gcp credential create <credential-id> <path-to-service-account.json>
```

### Comparing Jobs

To compare configurations between jobs:

```bash
jenkee job-diff <job1> <job2>
```

## Common Task Patterns

### Pattern 1: Find and inspect a job

```bash
jenkee list-views
jenkee list-jobs <view> | grep <pattern>
jenkee job-status <job-name>
jenkee list-builds <job-name>
```

### Pattern 2: Debug failed build

```bash
jenkee job-status <job-name>
jenkee list-builds <job-name>
jenkee console <job-name> <failed-build-number>
```

### Pattern 3: Clone and modify job

```bash
jenkee copy-job <source-job> <new-job-name>
# ALWAYS get fresh config before modifying
jenkee get-job <new-job-name> > config.xml
# Edit config.xml
jenkee update-job <new-job-name> < config.xml
```

### Pattern 4: Operate on a specific site when multiple profiles exist

```bash
jenkee profile list
jenkee profile use <name>
jenkee job-status <job-name>   # now targets <name>'s Jenkins
```

## Advanced Features (High-Risk Operations)

jenkee includes advanced features that are **hidden by default** because they involve destructive operations, deletion, or executing arbitrary code. These features require explicit access and user confirmation.

### Accessing Advanced Features

To view advanced features documentation:

```bash
# View all commands including advanced ones
jenkee help --all
```

### Advanced Feature Categories

**Advanced features typically include:**
- Job deletion commands
- Build deletion or cleanup operations
- Groovy script execution (arbitrary code on Jenkins server)
- Bulk operations that affect multiple resources
- System-level configuration changes

### MANDATORY Safety Protocol for Advanced Features

**Before using ANY advanced feature, you MUST:**

1. **Discover the feature exists:**
   - Run `jenkee help --all`
   - Read the complete documentation for the specific command with `jenkee help <command>`

2. **Verify it's the only solution:**
   - Confirm there is NO standard (non-advanced) command that can accomplish the task
   - Check `jenkee help` (without --all) for alternatives

3. **Confirm the target site:**
   - If the user has more than one profile configured, run `jenkee profile current` (or read the `Active profile: ...` banner jenkee prints before the confirmation prompt) and confirm it matches the site the user actually means
   - A destructive command run against the wrong profile is not reversible by re-running it against the right one

4. **Present detailed proposal to user:**
   - Explain what the command will do
   - State which Jenkins site/profile it will run against
   - List all resources that will be affected
   - Describe the risks and consequences
   - Explain whether the operation is reversible or irreversible
   - Show the exact command you plan to execute

5. **Get explicit user confirmation:**
   - Wait for user to review and approve
   - Do NOT proceed without clear approval
   - If user has any doubts, discuss alternatives first

6. **Execute with caution:**
   - Run the approved command exactly as presented
   - Monitor the output for errors
   - Report the results back to user

### Example: Groovy Command Protocol

The `groovy` command is the highest-risk advanced feature. Before using it:

```
❌ WRONG Approach:
User: "List all jobs"
AI: [Runs groovy script directly]

✅ CORRECT Approach:
User: "Find all jobs using credential X"
AI:
"I've checked `jenkee help` and there's no standard command for this.
I need to use the advanced `groovy` command.

Let me get the advanced documentation first:
[Runs: jenkee help --all]

Based on the documentation, I can write a groovy script that:
- Reads all job configurations (read-only)
- Searches for credential ID 'X'
- Returns matching job names
- Does NOT modify any data

Here's the script I propose:
[Show complete script]

This is read-only and safe. May I proceed?"

[Wait for user approval before executing]
```

### Risk Levels

**🟢 Low Risk (Standard Features):**
- Reading configurations, logs, status
- Listing resources
- No `--all` flag needed

**🟡 Medium Risk (May require --all):**
- Creating or copying resources
- Non-destructive modifications
- Requires careful review

**🔴 High Risk (Requires --all):**
- Deleting jobs or builds
- Groovy script execution
- Bulk operations
- System configuration changes
- **MUST follow safety protocol, including the target-site confirmation step**

## Important Guidelines

1. **Run `jenkee help` (and `jenkee help <command>` for unfamiliar commands)** — it reflects the exact version installed, so trust it over anything memorized here
2. **Verify authentication** with `jenkee auth`
3. **Check the active profile** with `jenkee profile current` whenever the user works with more than one Jenkins site, and before any destructive command
4. **Advanced features require `--all` flag** - Run `jenkee help --all` to access
5. **Advanced features require explicit user approval** - Follow the mandatory safety protocol above
6. **Job names are case-sensitive** - Use exact names when referencing jobs
7. **XML editing requires care** - Always backup configuration before modifying

## Version Compatibility

This skill covers the command surface as of the version it shipped with. `jenkee help` and `jenkee help <command>` are always accurate for whatever version is actually installed — when in doubt about exact syntax or whether a command still exists, defer to their output over this document.
