---
name: jenkins-helper
description: Operate Jenkins through the installed jenkee or jks CLI to inspect jobs, builds, logs, profiles, credentials, and configuration, or to perform explicitly authorized changes. Use when the user asks to work with Jenkins or jenkee, or uses jks in a Jenkins context. Do not use for generic CI/CD questions that do not require this CLI.
---

# Jenkins Helper

Use `jenkee` to carry out Jenkins work. `jks` is an equivalent alias.

## Boundaries

- Treat `jenkee help` and `jenkee help <command>` as authoritative for the installed version.
- This skill does not install `jenkee` or create credential files unless the user explicitly asks for setup help.
- Never display, log, or place Jenkins API tokens in commands, conversation text, or tracked files.
- Do not assume which Jenkins site the user means when multiple profiles exist.
- Do not rely on an agent hook as the only safeguard. Follow the safety protocol below even when a hook is installed.

## Establish the environment

Before the first Jenkins operation in a session:

1. Check that the CLI exists with `command -v jenkee`.
2. Run `jenkee help` to discover the current command surface.
3. Before a command that contacts Jenkins, verify access with `jenkee auth` unless successful access is already established in the session.
4. When profiles may be in use, or before any mutation, run `jenkee profile current` and report the resolved profile and URL.

If the CLI or authentication is unavailable, explain the failure and stop. Do not install software or write credentials without a separate user request.

## Profiles

Use these commands to inspect existing profiles:

```bash
jenkee profile list
jenkee profile current
```

Prefer a one-command override when the task names a specific site but does not ask to change persistent state:

```bash
jenkee --profile <name> <command>
```

Use `jenkee profile use <name>` or `jenkee profile use --default` only when the user asks to change the persistent active profile. If a requested profile is missing or invalid, stop instead of falling back to another site.

## Common operations

Inspect and troubleshoot:

```bash
jenkee list-views
jenkee list-jobs <view-name>
jenkee list-jobs --all
jenkee job-status <job-name>
jenkee list-builds <job-name>
jenkee console <job-name> [build-number]
jenkee job-diff <job-a> <job-b>
```

Trigger and stop builds:

```bash
jenkee build <job-name>
jenkee stop-builds <job-name> [job-name ...]
```

Manage jobs and views:

```bash
jenkee create-job <job-name> < config.xml
jenkee copy-job <source-job> <new-job-name>
jenkee add-job-to-view <view-name> <job-name> [job-name ...]
```

Inspect credentials and domains:

```bash
jenkee domain list
jenkee list-credentials [domain-name]
jenkee describe-credentials <credential-id>
jenkee gcp credential create <credential-id> <service-account.json>
```

Run `jenkee help <command>` before using unfamiliar syntax. Some destructive commands are hidden from ordinary help; discover them with `jenkee help --all` only when the task requires them.

## Updating job configuration

Always fetch a fresh configuration immediately before editing. Never reuse an old XML copy because it may overwrite changes made through Jenkins or by another operator.

Use a temporary directory for the working copy:

```bash
work_dir=$(mktemp -d)
jenkee get-job <job-name> > "$work_dir/job-config.xml"
```

Make the smallest requested XML change, preserve unrelated structure, review the diff, then propose the exact `update-job` command. Remove the temporary directory after the task when it is no longer needed.

## Safety protocol

### Read-only commands

Listing, status, logs, and configuration reads may run once the target site is established. Report the site when it matters to interpreting the result.

### State-changing commands

Commands such as `build`, `stop-builds`, `create-job`, `copy-job`, `update-job`, view changes, and credential creation affect Jenkins state. Before running them:

- establish the active profile and URL;
- identify the resources and expected effect;
- show the exact command when the scope is not already unambiguous;
- obtain clarification if the user's request does not clearly authorize that exact target and change.

### High-risk commands

Treat deletion, Groovy execution, disabling or enabling jobs, domain mutations, credential deletion, and bulk cleanup as high risk. This includes at least:

- `delete-job`
- `delete-builds`
- `groovy`
- `disable-job` and `enable-job`
- `domain create`, `domain update`, and `domain delete`
- `gcp credential delete`

Before every high-risk execution:

1. Run `jenkee help --all` and read `jenkee help <command>`.
2. Verify there is no safer standard command that satisfies the request.
3. Resolve and state the active profile and Jenkins URL.
4. List every known affected resource, consequence, and whether recovery is possible.
5. Show the exact command or complete Groovy script.
6. Ask for explicit approval and wait for it.
7. Execute only the approved command. Add `--yes-i-really-mean-it` only after approval when the CLI requires it.

Groovy is high risk even when intended to be read-only because it executes arbitrary server-side code. Never use Groovy merely as a shortcut for an available standard command.

## Setup guidance

If the user asks how to install the CLI, recommend an isolated CLI installer:

```bash
pipx install jenkee
```

If the user asks how to configure authentication or profiles, explain the `.env` layout using placeholders. Do not request the token in chat, write the file for them, or include a real token in an example.

Default configuration path:

```text
~/.jenkins-inspector/.env
```

Named profile path:

```text
~/.jenkins-inspector/profiles/<name>.env
```

Expected keys:

```dotenv
JENKINS_URL=https://jenkins.example.com/
JENKINS_USER_ID=your-user-id
JENKINS_API_TOKEN=<redacted>
```

## Reporting results

- State which Jenkins profile or URL was used for mutations and high-risk operations.
- Summarize the outcome, affected resources, and any partial failures.
- Redact credentials and sensitive command output.
- If execution stops before a mutation, clearly say that no Jenkins state was changed.
