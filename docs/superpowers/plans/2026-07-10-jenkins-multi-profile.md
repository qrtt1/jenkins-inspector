# Jenkins Multi-Profile Support Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let `jenkee` manage named connection profiles for multiple Jenkins sites (like `aws --profile`), while every existing single-site user keeps working with zero changes.

**Architecture:** `JenkinsConfig` gains a 3-tier resolution order — `JENKEE_PROFILE` env var (which a new global `--profile` CLI flag also writes into) beats a persistent `~/.jenkins-inspector/current_profile` state file, which beats the untouched default `~/.jenkins-inspector/.env`. A new `profile` command manages the persistent state and named profile files under `~/.jenkins-inspector/profiles/*.env`. Destructive commands print the resolved site before every confirmation prompt.

**Tech Stack:** Python 3.10+, `python-dotenv`, `pytest` (+ `testcontainers` for the existing Jenkins-docker integration suite — not needed for anything new in this plan).

Spec: `docs/superpowers/specs/2026-07-10-jenkins-multi-profile-design.md`

## Global Constraints

- Existing single-`.env` users must see **zero behavior change**: same commands, same file location (`~/.jenkins-inspector/.env`), same output, no required migration step.
- No feature reads or migrates the old ad-hoc `.env.*.bak` files from office-mbp; users create fresh named profiles.
- No cross-machine sync of any kind; profiles are local per machine.
- Resolution order, highest wins: `--profile <name>` flag → `JENKEE_PROFILE` env var → `~/.jenkins-inspector/current_profile` state file → default `~/.jenkins-inspector/.env`. (The flag and the env var collapse to the same check because the flag is implemented by setting the env var — see Task 4.)
- A named profile that is requested (via flag, env var, or state file) but whose file is missing is a **fatal error** — never silently fall back to the default.
- Destructive commands (`delete-job`, `delete-builds`, `groovy`, `disable-job`, `enable-job`, `domain create/update/delete`, `gcp credential delete`) must show the resolved site right before their confirmation prompt, even when it's the default profile.
- Non-destructive commands show the resolved site only when a **named** profile is active (default-profile users see no new output).
- Never accept Jenkins credentials as CLI arguments; profile files are always hand-edited by the user (same principle already used for the top-level `.env`).

---

### Task 1: `JenkinsConfig` profile resolution

**Files:**
- Modify: `jenkins_tools/core.py:90-119` (the `JenkinsConfig` class)
- Test: `tests/test_jenkins_config_profiles.py` (new)

**Interfaces:**
- Produces:
  - `JenkinsConfig.default_base_dir() -> Path` (staticmethod, returns `Path.home() / ".jenkins-inspector"`)
  - `JenkinsConfig(base_dir: Optional[Path] = None)` — `base_dir` is test-injection only; every production call site keeps calling `JenkinsConfig()`
  - New attributes after construction: `config.base_dir: Path`, `config.profiles_dir: Path` (`base_dir / "profiles"`), `config.current_profile_path: Path` (`base_dir / "current_profile"`), `config.profile_name: Optional[str]` (`None` means default `.env` is active), `config.profile_source: str` (one of `"env-override"`, `"persistent"`, `"default"`)
  - Existing attributes unchanged in name and meaning: `config.env_path`, `config.legacy_env_path`, `config.jenkins_url`, `config.username`, `config.api_token`, `config.is_configured()`, `config.get_auth_args()`
  - Side effects: exits the process with code 1 and a stderr message when a requested named profile's file doesn't exist; prints `Active profile: <name> (<url>)` to stderr when a named profile loaded successfully

- [ ] **Step 1: Write the failing tests**

Create `tests/test_jenkins_config_profiles.py`:

```python
"""
測試 JenkinsConfig 的 profile 解析邏輯

純檔案系統操作，不需要真的 Jenkins container，跑起來很快。
"""
import pytest

from jenkins_tools.core import JenkinsConfig


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    """每個測試都從乾淨的環境變數開始，不受開發者本機 shell 影響"""
    for key in ("JENKINS_URL", "JENKINS_USER_ID", "JENKINS_API_TOKEN", "JENKEE_PROFILE"):
        monkeypatch.delenv(key, raising=False)


def _write_profile(base_dir, name, url):
    profiles_dir = base_dir / "profiles"
    profiles_dir.mkdir(parents=True, exist_ok=True)
    (profiles_dir / f"{name}.env").write_text(
        f"JENKINS_URL={url}\nJENKINS_USER_ID=u\nJENKINS_API_TOKEN=t\n"
    )


def test_default_when_no_profile_state(tmp_path):
    (tmp_path / ".env").write_text(
        "JENKINS_URL=http://default/\nJENKINS_USER_ID=u\nJENKINS_API_TOKEN=t\n"
    )

    config = JenkinsConfig(base_dir=tmp_path)

    assert config.profile_name is None
    assert config.profile_source == "default"
    assert config.jenkins_url == "http://default/"


def test_env_var_overrides_and_loads_named_profile(tmp_path, monkeypatch):
    _write_profile(tmp_path, "pchome-prod", "http://pchome/")
    monkeypatch.setenv("JENKEE_PROFILE", "pchome-prod")

    config = JenkinsConfig(base_dir=tmp_path)

    assert config.profile_name == "pchome-prod"
    assert config.profile_source == "env-override"
    assert config.jenkins_url == "http://pchome/"


def test_current_profile_state_file_used_without_env_override(tmp_path):
    _write_profile(tmp_path, "ops", "http://ops/")
    (tmp_path / "current_profile").write_text("ops\n")

    config = JenkinsConfig(base_dir=tmp_path)

    assert config.profile_name == "ops"
    assert config.profile_source == "persistent"
    assert config.jenkins_url == "http://ops/"


def test_env_var_takes_precedence_over_state_file(tmp_path, monkeypatch):
    _write_profile(tmp_path, "ops", "http://ops/")
    _write_profile(tmp_path, "pchome-prod", "http://pchome/")
    (tmp_path / "current_profile").write_text("ops\n")
    monkeypatch.setenv("JENKEE_PROFILE", "pchome-prod")

    config = JenkinsConfig(base_dir=tmp_path)

    assert config.profile_name == "pchome-prod"
    assert config.profile_source == "env-override"


def test_missing_profile_from_env_var_exits_with_error(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("JENKEE_PROFILE", "does-not-exist")

    with pytest.raises(SystemExit) as exc_info:
        JenkinsConfig(base_dir=tmp_path)

    assert exc_info.value.code == 1
    err = capsys.readouterr().err
    assert "does-not-exist" in err
    assert "jenkee profile list" in err


def test_missing_profile_from_state_file_exits_with_error(tmp_path, capsys):
    (tmp_path / "current_profile").write_text("ghost\n")

    with pytest.raises(SystemExit) as exc_info:
        JenkinsConfig(base_dir=tmp_path)

    assert exc_info.value.code == 1
    err = capsys.readouterr().err
    assert "ghost" in err
    assert "profile use --default" in err


def test_active_profile_banner_printed_for_named_profile(tmp_path, monkeypatch, capsys):
    _write_profile(tmp_path, "ops", "http://ops/")
    monkeypatch.setenv("JENKEE_PROFILE", "ops")

    JenkinsConfig(base_dir=tmp_path)

    assert "Active profile: ops (http://ops/)" in capsys.readouterr().err


def test_no_banner_for_default_profile(tmp_path, capsys):
    (tmp_path / ".env").write_text(
        "JENKINS_URL=http://default/\nJENKINS_USER_ID=u\nJENKINS_API_TOKEN=t\n"
    )

    JenkinsConfig(base_dir=tmp_path)

    assert "Active profile" not in capsys.readouterr().err


def test_default_base_dir_points_at_home_dot_jenkins_inspector():
    assert JenkinsConfig.default_base_dir().name == ".jenkins-inspector"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_jenkins_config_profiles.py -v`
Expected: FAIL with `TypeError: __init__() got an unexpected keyword argument 'base_dir'` (and `AttributeError: default_base_dir` for the last test).

- [ ] **Step 3: Implement the resolution logic**

Replace the `JenkinsConfig` class in `jenkins_tools/core.py` (currently lines 90-119) with:

```python
class JenkinsConfig:
    """Manage Jenkins configuration"""

    @staticmethod
    def default_base_dir() -> Path:
        """Directory holding .env, profiles/, and current_profile"""
        return Path.home() / ".jenkins-inspector"

    def __init__(self, base_dir: Optional[Path] = None):
        # Load .env from ~/.jenkins-inspector/ only.
        # If a legacy file exists at ~/.jenkins-studio/.env, we intentionally do NOT load it.
        self.legacy_env_path = Path.home() / ".jenkins-studio" / ".env"
        self.base_dir = base_dir or self.default_base_dir()
        self.env_path = self.base_dir / ".env"
        self.profiles_dir = self.base_dir / "profiles"
        self.current_profile_path = self.base_dir / "current_profile"

        self.profile_name, self.profile_source, error = self._resolve_active_profile()

        if error:
            print(f"Error: {error}", file=sys.stderr)
            sys.exit(1)

        resolved_env_path = (
            self.profiles_dir / f"{self.profile_name}.env"
            if self.profile_name
            else self.env_path
        )

        # override=False: 環境變數優先於 .env 檔案（重要：讓測試可以覆蓋設定）
        load_dotenv(resolved_env_path, override=False)
        self.jenkins_url = os.getenv("JENKINS_URL")
        self.username = os.getenv("JENKINS_USER_ID")
        self.api_token = os.getenv("JENKINS_API_TOKEN")

        if self.profile_name:
            print(f"Active profile: {self.profile_name} ({self.jenkins_url})", file=sys.stderr)

    def _resolve_active_profile(self) -> tuple[Optional[str], str, Optional[str]]:
        """
        Determine which profile should be loaded.

        Returns:
            (profile_name, source, error_message). profile_name is None when the
            default ~/.jenkins-inspector/.env should be used. error_message is set
            when a named profile was requested but its file is missing -- callers
            must treat that as fatal, never fall back silently to the default.
        """
        env_profile = os.getenv("JENKEE_PROFILE", "").strip()
        if env_profile:
            profile_path = self.profiles_dir / f"{env_profile}.env"
            if not profile_path.exists():
                return None, "env-override", (
                    f"profile '{env_profile}' not found at {profile_path}.\n"
                    f"Run 'jenkee profile list' to see available profiles, "
                    f"or unset JENKEE_PROFILE to use the default config."
                )
            return env_profile, "env-override", None

        if self.current_profile_path.exists():
            state_profile = self.current_profile_path.read_text().strip()
            if state_profile:
                profile_path = self.profiles_dir / f"{state_profile}.env"
                if not profile_path.exists():
                    return None, "persistent", (
                        f"current profile '{state_profile}' (set via 'jenkee profile use') "
                        f"no longer exists at {profile_path}.\n"
                        f"Run 'jenkee profile use --default' or 'jenkee profile use <name>' to fix this."
                    )
                return state_profile, "persistent", None

        return None, "default", None

    @property
    def jenkins_cli_jar_url(self) -> str:
        """Get Jenkins CLI JAR download URL"""
        return f"{self.jenkins_url}jnlpJars/jenkins-cli.jar"

    def is_configured(self) -> bool:
        """Check if Jenkins credentials are configured"""
        return bool(self.jenkins_url and self.username and self.api_token)

    def get_auth_args(self) -> list[str]:
        """Get authentication arguments for jenkins-cli"""
        if not self.is_configured():
            return []
        return ["-auth", f"{self.username}:{self.api_token}"]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_jenkins_config_profiles.py -v`
Expected: PASS (all 9 tests)

- [ ] **Step 5: Run the full existing suite's fast subset to check for import/syntax regressions**

Run: `python -c "import jenkins_tools.core"`
Expected: no output, exit code 0 (sanity check that the module still imports cleanly before the slower docker suite runs in Task 6)

- [ ] **Step 6: Commit**

```bash
git add jenkins_tools/core.py tests/test_jenkins_config_profiles.py
git commit -m "feat: add profile resolution to JenkinsConfig"
```

---

### Task 2: Safety banner on destructive commands

**Files:**
- Modify: `jenkins_tools/core.py:32-87` (`DangerousCommandMixin.require_confirmation`)
- Modify: `jenkins_tools/commands/delete_job.py:47`
- Modify: `jenkins_tools/commands/delete_builds.py:50`
- Modify: `jenkins_tools/commands/groovy.py:64`
- Modify: `jenkins_tools/commands/disable_job.py:50`
- Modify: `jenkins_tools/commands/enable_job.py:50`
- Modify: `jenkins_tools/commands/domain.py:163,231,318`
- Modify: `jenkins_tools/commands/gcp/credential.py:389`
- Test: `tests/test_dangerous_command_profile_banner.py` (new)

**Interfaces:**
- Consumes: `JenkinsConfig(base_dir=...)`, `.profile_name`, `.jenkins_url` from Task 1
- Produces: `DangerousCommandMixin.require_confirmation(operation_description: str, config: Optional[JenkinsConfig] = None) -> bool` — the `config` parameter is new and optional; every existing call site is updated to pass it, but the parameter defaulting to `None` means the method still works if some future caller omits it

**Design note:** `JenkinsConfig.__init__` already prints `Active profile: <name> (<url>)` to stderr for named profiles (Task 1). Every command constructs `JenkinsConfig()` before doing anything else, so by the time `require_confirmation` runs, that banner has already been shown for named profiles. The only gap `require_confirmation` needs to fill is the **default** profile case, which `JenkinsConfig` intentionally stays silent about (to keep default-profile users' output unchanged). So `require_confirmation` only prints when `config.profile_name is None`, and it does so unconditionally -- before checking `--yes-i-really-mean-it` -- so the site is visible even in non-interactive/scripted runs.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_dangerous_command_profile_banner.py`:

```python
"""
測試 DangerousCommandMixin.require_confirmation 的 profile 可見度

用一個假的 dangerous command 直接測試 mixin，不需要真的 Jenkins。
"""
import pytest

from jenkins_tools.core import Command, DangerousCommandMixin, JenkinsConfig


class _DummyDangerousCommand(DangerousCommandMixin, Command):
    def __init__(self, args=None):
        self.args = args or []
        super().__init__()

    def execute(self) -> int:
        return 0


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for key in ("JENKINS_URL", "JENKINS_USER_ID", "JENKINS_API_TOKEN", "JENKEE_PROFILE"):
        monkeypatch.delenv(key, raising=False)


def test_shows_default_profile_banner_before_prompt(tmp_path, capsys):
    (tmp_path / ".env").write_text(
        "JENKINS_URL=http://default/\nJENKINS_USER_ID=u\nJENKINS_API_TOKEN=t\n"
    )
    config = JenkinsConfig(base_dir=tmp_path)
    capsys.readouterr()  # discard construction-time output

    cmd = _DummyDangerousCommand(["--yes-i-really-mean-it"])
    result = cmd.require_confirmation("delete something", config)

    assert result is True
    assert "Active profile: default (http://default/)" in capsys.readouterr().out


def test_does_not_duplicate_banner_for_named_profile(tmp_path, monkeypatch, capsys):
    profiles_dir = tmp_path / "profiles"
    profiles_dir.mkdir()
    (profiles_dir / "ops.env").write_text(
        "JENKINS_URL=http://ops/\nJENKINS_USER_ID=u\nJENKINS_API_TOKEN=t\n"
    )
    monkeypatch.setenv("JENKEE_PROFILE", "ops")
    config = JenkinsConfig(base_dir=tmp_path)
    capsys.readouterr()  # discard the banner JenkinsConfig already printed

    cmd = _DummyDangerousCommand(["--yes-i-really-mean-it"])
    cmd.require_confirmation("delete something", config)

    assert "Active profile" not in capsys.readouterr().out


def test_banner_shows_even_with_skip_confirmation_flag(tmp_path, capsys):
    (tmp_path / ".env").write_text(
        "JENKINS_URL=http://default/\nJENKINS_USER_ID=u\nJENKINS_API_TOKEN=t\n"
    )
    config = JenkinsConfig(base_dir=tmp_path)
    capsys.readouterr()

    cmd = _DummyDangerousCommand(["--yes-i-really-mean-it"])
    cmd.require_confirmation("delete something", config)

    assert "Active profile: default" in capsys.readouterr().out


def test_backward_compatible_without_config_argument():
    """既有呼叫方式（不傳 config）行為必須完全不變"""
    cmd = _DummyDangerousCommand(["--yes-i-really-mean-it"])
    assert cmd.require_confirmation("do something") is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_dangerous_command_profile_banner.py -v`
Expected: FAIL with `TypeError: require_confirmation() takes 2 positional arguments but 3 were given`

- [ ] **Step 3: Implement `require_confirmation`**

Replace `require_confirmation` in `jenkins_tools/core.py` (currently lines 63-87) with:

```python
    def require_confirmation(
        self, operation_description: str, config: "Optional[JenkinsConfig]" = None
    ) -> bool:
        """
        Check for confirmation or prompt for interactive confirmation

        Args:
            operation_description: Description of the operation (e.g., "delete job 'test-job'")
            config: The JenkinsConfig in effect for this command. When it's the
                default profile, JenkinsConfig stays silent about it (to avoid
                changing output for default-profile users elsewhere), so this
                method prints the active site here instead -- unconditionally,
                even when --yes-i-really-mean-it skips the interactive prompt.
                Named profiles already announced themselves when JenkinsConfig
                was constructed, so nothing further is printed here for them.

        Returns:
            True if confirmed (either via flag or user input), False if cancelled
        """
        if config is not None and config.profile_name is None:
            print(f"Active profile: default ({config.jenkins_url})")

        # Check if confirmation flag was present
        if self._skip_confirmation:
            return True

        # Interactive confirmation
        try:
            response = input(f"Are you sure you want to {operation_description}? (y/N): ")
            if response.lower() in ('y', 'yes'):
                return True
            else:
                print("Operation cancelled.")
                return False
        except (EOFError, KeyboardInterrupt):
            print("\nOperation cancelled.")
            return False
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_dangerous_command_profile_banner.py -v`
Expected: PASS (all 4 tests)

- [ ] **Step 5: Wire `config` into every call site**

Each of these is the same one-line change -- pass the already-in-scope `config` variable as the second argument:

`jenkins_tools/commands/delete_job.py:47`
```python
# before
        if not self.require_confirmation(operation_desc):
# after
        if not self.require_confirmation(operation_desc, config):
```

`jenkins_tools/commands/delete_builds.py:50`
```python
# before
        if not self.require_confirmation(operation_desc):
# after
        if not self.require_confirmation(operation_desc, config):
```

`jenkins_tools/commands/groovy.py:64`
```python
# before
        if not self.require_confirmation(operation_desc):
# after
        if not self.require_confirmation(operation_desc, config):
```

`jenkins_tools/commands/disable_job.py:50`
```python
# before
        if not self.require_confirmation(operation_desc):
# after
        if not self.require_confirmation(operation_desc, config):
```

`jenkins_tools/commands/enable_job.py:50`
```python
# before
        if not self.require_confirmation(operation_desc):
# after
        if not self.require_confirmation(operation_desc, config):
```

`jenkins_tools/commands/domain.py:163`
```python
# before
        if not self.require_confirmation(f"create domain '{domain_name}'"):
# after
        if not self.require_confirmation(f"create domain '{domain_name}'", config):
```

`jenkins_tools/commands/domain.py:231`
```python
# before
        if not self.require_confirmation(f"update domain '{domain_name}'"):
# after
        if not self.require_confirmation(f"update domain '{domain_name}'", config):
```

`jenkins_tools/commands/domain.py:318`
```python
# before
        if not self.require_confirmation(f"delete domain '{domain_name}'"):
# after
        if not self.require_confirmation(f"delete domain '{domain_name}'", config):
```

`jenkins_tools/commands/gcp/credential.py:389`
```python
# before
        if not self.require_confirmation(operation_desc):
# after
        if not self.require_confirmation(operation_desc, config):
```

- [ ] **Step 6: Confirm none of these files broke their own imports**

Run: `python -c "import jenkins_tools.commands.delete_job, jenkins_tools.commands.delete_builds, jenkins_tools.commands.groovy, jenkins_tools.commands.disable_job, jenkins_tools.commands.enable_job, jenkins_tools.commands.domain, jenkins_tools.commands.gcp.credential"`
Expected: no output, exit code 0

- [ ] **Step 7: Commit**

```bash
git add jenkins_tools/core.py jenkins_tools/commands/delete_job.py jenkins_tools/commands/delete_builds.py jenkins_tools/commands/groovy.py jenkins_tools/commands/disable_job.py jenkins_tools/commands/enable_job.py jenkins_tools/commands/domain.py jenkins_tools/commands/gcp/credential.py tests/test_dangerous_command_profile_banner.py
git commit -m "feat: show active site before every destructive confirmation"
```

---

### Task 3: `ProfileCommand` (list / use / current)

**Files:**
- Create: `jenkins_tools/commands/profile.py`
- Modify: `jenkins_tools/commands/__init__.py`
- Test: `tests/test_profile_command_unit.py` (new)

**Interfaces:**
- Consumes: `JenkinsConfig.default_base_dir()`, `JenkinsConfig(base_dir=...)`, `.profile_name`, `.profile_source`, `.profiles_dir`, `.env_path`, `.jenkins_url` from Task 1
- Produces: `ProfileCommand(args: list[str] = None, base_dir: Optional[Path] = None)` with `.execute() -> int`, handling subcommands `list`, `use <name>`, `use --default`, `current`. `base_dir` is test-injection only; Task 4's `cli.py` wiring always omits it.

This task tests `ProfileCommand` by importing and calling it directly (no subprocess, no `cli.py` change yet -- that's Task 4, since `profile` isn't dispatchable from the CLI until then).

- [ ] **Step 1: Write the failing tests**

Create `tests/test_profile_command_unit.py`:

```python
"""
測試 ProfileCommand 的 list / use / current 邏輯

直接呼叫 ProfileCommand，不經過 cli.py（cli.py 的 dispatch 在 Task 4 才接上）。
"""
import pytest

from jenkins_tools.commands.profile import ProfileCommand


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for key in ("JENKINS_URL", "JENKINS_USER_ID", "JENKINS_API_TOKEN", "JENKEE_PROFILE"):
        monkeypatch.delenv(key, raising=False)


def _write_profile(base_dir, name, url):
    profiles_dir = base_dir / "profiles"
    profiles_dir.mkdir(parents=True, exist_ok=True)
    (profiles_dir / f"{name}.env").write_text(
        f"JENKINS_URL={url}\nJENKINS_USER_ID=u\nJENKINS_API_TOKEN=t\n"
    )


def test_list_shows_default_active_when_nothing_configured(tmp_path, capsys):
    exit_code = ProfileCommand(["list"], base_dir=tmp_path).execute()

    assert exit_code == 0
    assert "default (active)" in capsys.readouterr().out


def test_list_shows_named_profiles(tmp_path, capsys):
    _write_profile(tmp_path, "ops", "http://ops/")
    _write_profile(tmp_path, "pchome-prod", "http://pchome/")

    exit_code = ProfileCommand(["list"], base_dir=tmp_path).execute()

    out = capsys.readouterr().out
    assert exit_code == 0
    assert "ops" in out
    assert "pchome-prod" in out
    assert "default (active)" in out  # 還沒切換前，預設仍是 active


def test_list_marks_env_override_as_active(tmp_path, monkeypatch, capsys):
    _write_profile(tmp_path, "ops", "http://ops/")
    monkeypatch.setenv("JENKEE_PROFILE", "ops")

    ProfileCommand(["list"], base_dir=tmp_path).execute()

    assert "ops (active)" in capsys.readouterr().out


def test_use_switches_persistent_state(tmp_path, capsys):
    _write_profile(tmp_path, "ops", "http://ops/")

    exit_code = ProfileCommand(["use", "ops"], base_dir=tmp_path).execute()

    assert exit_code == 0
    assert (tmp_path / "current_profile").read_text().strip() == "ops"
    assert "ops" in capsys.readouterr().out


def test_use_default_clears_state(tmp_path):
    (tmp_path / "current_profile").write_text("ops\n")

    exit_code = ProfileCommand(["use", "--default"], base_dir=tmp_path).execute()

    assert exit_code == 0
    assert not (tmp_path / "current_profile").exists()


def test_use_unknown_profile_fails_with_creation_guidance(tmp_path, capsys):
    exit_code = ProfileCommand(["use", "does-not-exist"], base_dir=tmp_path).execute()

    err = capsys.readouterr().err
    assert exit_code == 1
    assert "does-not-exist" in err
    assert "mkdir -p" in err


def test_current_shows_default_when_nothing_active(tmp_path, capsys):
    exit_code = ProfileCommand(["current"], base_dir=tmp_path).execute()

    assert exit_code == 0
    assert "Profile: default" in capsys.readouterr().out


def test_current_shows_named_profile_and_source(tmp_path, monkeypatch, capsys):
    _write_profile(tmp_path, "ops", "http://ops/")
    monkeypatch.setenv("JENKEE_PROFILE", "ops")

    exit_code = ProfileCommand(["current"], base_dir=tmp_path).execute()

    out = capsys.readouterr().out
    assert exit_code == 0
    assert "Profile: ops" in out
    assert "http://ops/" in out


def test_current_fails_clearly_when_state_file_is_broken(tmp_path, capsys):
    (tmp_path / "current_profile").write_text("ghost\n")

    with pytest.raises(SystemExit) as exc_info:
        ProfileCommand(["current"], base_dir=tmp_path).execute()

    assert exc_info.value.code == 1
    assert "ghost" in capsys.readouterr().err


def test_missing_subcommand_is_an_error(tmp_path, capsys):
    exit_code = ProfileCommand([], base_dir=tmp_path).execute()

    assert exit_code == 1
    assert "Usage" in capsys.readouterr().err
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_profile_command_unit.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'jenkins_tools.commands.profile'`

- [ ] **Step 3: Create `jenkins_tools/commands/profile.py`**

```python
"""Profile command - manage named Jenkins connection profiles"""

import os
import sys
from pathlib import Path
from typing import Optional

from jenkins_tools.core import Command, JenkinsConfig


class ProfileCommand(Command):
    """Manage named Jenkins connection profiles (multi-site support)"""

    def __init__(self, args=None, base_dir: Optional[Path] = None):
        """
        Initialize with command line arguments

        Args:
            args: List of command arguments (sys.argv[2:]).
                  First element is the subcommand: list | use | current
            base_dir: Override for ~/.jenkins-inspector (test injection only;
                      production callers always omit this)
        """
        self.args = args or []
        self.base_dir = base_dir or JenkinsConfig.default_base_dir()

    def execute(self) -> int:
        """Execute profile command"""
        if not self.args:
            print("Error: Missing subcommand", file=sys.stderr)
            print("Usage: jenkee profile <list|use|current>", file=sys.stderr)
            return 1

        subcommand = self.args[0]
        rest = self.args[1:]

        if subcommand == "list":
            return self._list()
        elif subcommand == "use":
            return self._use(rest)
        elif subcommand == "current":
            return self._current()
        else:
            print(f"Error: Unknown profile subcommand '{subcommand}'", file=sys.stderr)
            print("Usage: jenkee profile <list|use|current>", file=sys.stderr)
            return 1

    def _list(self) -> int:
        """List all configured profiles, marking which one is active"""
        profiles_dir = self.base_dir / "profiles"
        active_name = self._active_name_hint()

        names = ["default"]
        if profiles_dir.exists():
            names += sorted(p.stem for p in profiles_dir.glob("*.env"))

        print("Available profiles:")
        for name in names:
            marker = " (active)" if name == (active_name or "default") else ""
            print(f"  {name}{marker}")
        return 0

    def _use(self, rest: list[str]) -> int:
        """Switch the persistent active profile"""
        if not rest:
            print("Error: Missing profile name", file=sys.stderr)
            print("Usage: jenkee profile use <name>", file=sys.stderr)
            print("       jenkee profile use --default", file=sys.stderr)
            return 1

        current_profile_path = self.base_dir / "current_profile"
        target = rest[0]

        if target == "--default":
            if current_profile_path.exists():
                current_profile_path.unlink()
            print("✓ Switched to default profile")
            print(f"  Using: {self.base_dir / '.env'}")
            return 0

        profile_path = self.base_dir / "profiles" / f"{target}.env"
        if not profile_path.exists():
            print(f"Error: Profile '{target}' not found at {profile_path}", file=sys.stderr)
            print("", file=sys.stderr)
            print("Create it first:", file=sys.stderr)
            print(f"  mkdir -p {self.base_dir / 'profiles'}", file=sys.stderr)
            print(f"  cat > {profile_path} << 'EOF'", file=sys.stderr)
            print("  JENKINS_URL=http://your-jenkins-server:8080/", file=sys.stderr)
            print("  JENKINS_USER_ID=your_email@example.com", file=sys.stderr)
            print("  JENKINS_API_TOKEN=your_api_token", file=sys.stderr)
            print("  EOF", file=sys.stderr)
            return 1

        self.base_dir.mkdir(parents=True, exist_ok=True)
        current_profile_path.write_text(f"{target}\n")
        print(f"✓ Switched to profile '{target}'")
        print(f"  Using: {profile_path}")
        return 0

    def _current(self) -> int:
        """Show which profile is currently active"""
        config = JenkinsConfig(base_dir=self.base_dir)  # exits with a clear error if broken

        if config.profile_name:
            source_label = {
                "env-override": "JENKEE_PROFILE / --profile",
                "persistent": "jenkee profile use",
            }.get(config.profile_source, config.profile_source)
            print(f"Profile: {config.profile_name}")
            print(f"Source: {source_label}")
            print(f"Config file: {config.profiles_dir / f'{config.profile_name}.env'}")
        else:
            print("Profile: default")
            print("Source: default (no override active)")
            print(f"Config file: {config.env_path}")

        print(f"Jenkins URL: {config.jenkins_url or '(not configured)'}")
        return 0

    def _active_name_hint(self) -> Optional[str]:
        """
        Best-effort lookup of the active profile name without validating that
        its file still exists. `list` must keep working even when the current
        selection is broken -- that's the whole point of `list` as a recovery tool.
        """
        env_override = os.getenv("JENKEE_PROFILE", "").strip()
        if env_override:
            return env_override

        current_profile_path = self.base_dir / "current_profile"
        if current_profile_path.exists():
            stored = current_profile_path.read_text().strip()
            if stored:
                return stored

        return None
```

- [ ] **Step 4: Register `ProfileCommand` in `jenkins_tools/commands/__init__.py`**

Add the import (after the `DevQACommand` import):

```python
from jenkins_tools.commands.dev_qa import DevQACommand
from jenkins_tools.commands.profile import ProfileCommand
```

Add to `__all__` (after `"DevQACommand"`):

```python
    "DevQACommand",
    "ProfileCommand",
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_profile_command_unit.py -v`
Expected: PASS (all 10 tests)

- [ ] **Step 6: Commit**

```bash
git add jenkins_tools/commands/profile.py jenkins_tools/commands/__init__.py tests/test_profile_command_unit.py
git commit -m "feat: add ProfileCommand for listing/switching/inspecting Jenkins profiles"
```

---

### Task 4: Wire `--profile` flag and `profile` dispatch into `cli.py`

**Files:**
- Modify: `jenkins_tools/cli.py` (full rewrite of the dispatch logic)
- Test: `tests/test_profile_command_cli.py` (new)
- Test: `docs/test-plan-for-profile-management.md` (new)

**Interfaces:**
- Consumes: `ProfileCommand` from Task 3
- Produces: `jenkee profile <list|use|current>` and `jenkee --profile <name> <any-command>` work end-to-end through the installed `jenkee` console script

This is the first task that needs the real, installed CLI (`jenkee` on PATH via the editable install), so its tests use `subprocess.run(["jenkee", ...])`, matching the existing convention in `tests/test_help_flag.py`. None of these tests need the Jenkins docker container -- `profile` subcommands are pure filesystem operations -- so they isolate `~/.jenkins-inspector` by pointing `HOME` at a `tmp_path` for the subprocess, instead of touching the developer's real config.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_profile_command_cli.py`:

```python
"""
測試 --profile 全域 flag 與 profile 指令的 CLI 端到端行為

不需要 Jenkins container：把 HOME 導向 tmp_path，讓 ~/.jenkins-inspector
完全隔離於開發者本機的真實設定，同時也不需要 docker。
"""
import os
import subprocess


def _isolated_env(home_dir) -> dict:
    env = os.environ.copy()
    env["HOME"] = str(home_dir)
    for key in ("JENKINS_URL", "JENKINS_USER_ID", "JENKINS_API_TOKEN", "JENKEE_PROFILE"):
        env.pop(key, None)
    return env


def _write_profile(home_dir, name, url):
    profiles_dir = home_dir / ".jenkins-inspector" / "profiles"
    profiles_dir.mkdir(parents=True, exist_ok=True)
    (profiles_dir / f"{name}.env").write_text(
        f"JENKINS_URL={url}\nJENKINS_USER_ID=u\nJENKINS_API_TOKEN=t\n"
    )


def test_profile_list_via_cli(tmp_path):
    result = subprocess.run(
        ["jenkee", "profile", "list"],
        capture_output=True, text=True, env=_isolated_env(tmp_path),
    )

    assert result.returncode == 0
    assert "default (active)" in result.stdout


def test_profile_use_then_list_reflects_switch(tmp_path):
    _write_profile(tmp_path, "ops", "http://ops/")
    env = _isolated_env(tmp_path)

    use_result = subprocess.run(
        ["jenkee", "profile", "use", "ops"], capture_output=True, text=True, env=env,
    )
    assert use_result.returncode == 0

    list_result = subprocess.run(
        ["jenkee", "profile", "list"], capture_output=True, text=True, env=env,
    )
    assert "ops (active)" in list_result.stdout


def test_global_profile_flag_overrides_without_persisting(tmp_path):
    _write_profile(tmp_path, "ops", "http://ops/")
    env = _isolated_env(tmp_path)

    result = subprocess.run(
        ["jenkee", "--profile", "ops", "profile", "current"],
        capture_output=True, text=True, env=env,
    )

    assert result.returncode == 0
    assert "Profile: ops" in result.stdout
    state_file = tmp_path / ".jenkins-inspector" / "current_profile"
    assert not state_file.exists()  # 單次覆蓋不動持久狀態


def test_profile_flag_missing_value_is_an_error(tmp_path):
    result = subprocess.run(
        ["jenkee", "--profile"],
        capture_output=True, text=True, env=_isolated_env(tmp_path),
    )

    assert result.returncode == 1
    assert "--profile requires a value" in result.stderr


def test_unknown_command_still_errors_normally(tmp_path):
    """回歸驗證：--profile 抽取邏輯不能影響既有的未知指令錯誤處理"""
    result = subprocess.run(
        ["jenkee", "not-a-real-command"],
        capture_output=True, text=True, env=_isolated_env(tmp_path),
    )

    assert result.returncode == 1
    assert "Unknown command" in result.stderr
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_profile_command_cli.py -v`
Expected: FAIL -- `jenkee profile list` exits 1 with `Error: Unknown command 'profile'`

- [ ] **Step 3: Rewrite `jenkins_tools/cli.py`**

Replace the entire file with:

```python
"""Jenkins CLI main entry point"""

import os
import sys
from pathlib import Path

from jenkins_tools.commands import (
    AuthCommand,
    ListViewsCommand,
    ListJobsCommand,
    GetJobCommand,
    ListBuildsCommand,
    ConsoleCommand,
    JobStatusCommand,
    JobDiffCommand,
    ListCredentialsCommand,
    DescribeCredentialsCommand,
    AddJobToViewCommand,
    CopyJobCommand,
    UpdateJobCommand,
    BuildCommand,
    StopBuildsCommand,
    CreateJobCommand,
    DeleteJobCommand,
    DisableJobCommand,
    EnableJobCommand,
    DeleteBuildsCommand,
    GroovyCommand,
    DomainCommand,
    HelpCommand,
    PromptCommand,
    DevQACommand,
    ProfileCommand,
)
from jenkins_tools.commands.gcp import GCPCommand


def _extract_profile_flag(argv: list[str]) -> list[str]:
    """
    Pull a global `--profile <name>` flag out of argv, wherever it appears,
    and apply it as JENKEE_PROFILE for this process.

    This keeps every existing Command unaware of --profile entirely:
    JenkinsConfig already reads JENKEE_PROFILE from the environment, so a
    CLI flag and an exported env var end up on the exact same code path.
    """
    result = []
    i = 0
    while i < len(argv):
        if argv[i] == "--profile":
            if i + 1 >= len(argv):
                print("Error: --profile requires a value", file=sys.stderr)
                sys.exit(1)
            os.environ["JENKEE_PROFILE"] = argv[i + 1]
            i += 2
            continue
        result.append(argv[i])
        i += 1
    return result


def main():
    """Main entry point for CLI command"""
    program_name = Path(sys.argv[0]).name if sys.argv else "jenkee"

    argv = _extract_profile_flag(sys.argv[1:])

    if len(argv) < 1:
        # 沒有參數時顯示命令列表
        cmd = HelpCommand()
        sys.exit(cmd.execute())

    command = argv[0]

    # Handle global --help or -h flag
    if command in ("--help", "-h"):
        cmd = HelpCommand(argv[1:])
        sys.exit(cmd.execute())

    # Dispatch to appropriate command
    if command == "auth":
        cmd = AuthCommand()
        sys.exit(cmd.execute())
    elif command == "list-views":
        cmd = ListViewsCommand()
        sys.exit(cmd.execute())
    elif command == "list-jobs":
        cmd = ListJobsCommand(argv[1:])
        sys.exit(cmd.execute())
    elif command == "get-job":
        cmd = GetJobCommand(argv[1:])
        sys.exit(cmd.execute())
    elif command == "list-builds":
        cmd = ListBuildsCommand(argv[1:])
        sys.exit(cmd.execute())
    elif command == "console":
        cmd = ConsoleCommand(argv[1:])
        sys.exit(cmd.execute())
    elif command == "job-status":
        cmd = JobStatusCommand(argv[1:])
        sys.exit(cmd.execute())
    elif command == "job-diff":
        cmd = JobDiffCommand(argv[1:])
        sys.exit(cmd.execute())
    elif command == "list-credentials":
        cmd = ListCredentialsCommand(argv[1:])
        sys.exit(cmd.execute())
    elif command == "describe-credentials":
        cmd = DescribeCredentialsCommand(argv[1:])
        sys.exit(cmd.execute())
    elif command == "add-job-to-view":
        cmd = AddJobToViewCommand(argv[1:])
        sys.exit(cmd.execute())
    elif command == "copy-job":
        cmd = CopyJobCommand(argv[1:])
        sys.exit(cmd.execute())
    elif command == "update-job":
        cmd = UpdateJobCommand(argv[1:])
        sys.exit(cmd.execute())
    elif command == "build":
        cmd = BuildCommand(argv[1:])
        sys.exit(cmd.execute())
    elif command == "stop-builds":
        cmd = StopBuildsCommand(argv[1:])
        sys.exit(cmd.execute())
    elif command == "create-job":
        cmd = CreateJobCommand(argv[1:])
        sys.exit(cmd.execute())
    elif command == "delete-job":
        cmd = DeleteJobCommand(argv[1:])
        sys.exit(cmd.execute())
    elif command == "disable-job":
        cmd = DisableJobCommand(argv[1:])
        sys.exit(cmd.execute())
    elif command == "enable-job":
        cmd = EnableJobCommand(argv[1:])
        sys.exit(cmd.execute())
    elif command == "delete-builds":
        cmd = DeleteBuildsCommand(argv[1:])
        sys.exit(cmd.execute())
    elif command == "groovy":
        cmd = GroovyCommand(argv[1:])
        sys.exit(cmd.execute())
    elif command == "gcp":
        cmd = GCPCommand(argv[1:])
        sys.exit(cmd.execute())
    elif command == "domain":
        cmd = DomainCommand(argv[1:])
        sys.exit(cmd.execute())
    elif command == "profile":
        cmd = ProfileCommand(argv[1:])
        sys.exit(cmd.execute())
    elif command == "prompt":
        cmd = PromptCommand(argv[1:])
        sys.exit(cmd.execute())
    elif command == "help":
        cmd = HelpCommand(argv[1:])
        sys.exit(cmd.execute())
    elif command == "dev-qa":
        cmd = DevQACommand(argv[1:])
        sys.exit(cmd.execute())
    else:
        print(f"Error: Unknown command '{command}'", file=sys.stderr)
        print(f"Run '{program_name} help' to see available commands", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Reinstall the editable package so the console script picks up the change**

Run: `pip install -e .`
Expected: exits 0 (this project is already installed editable per `CODING_GUIDE.md`; this just re-registers `jenkee`/`jks`, no new dependency)

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_profile_command_cli.py -v`
Expected: PASS (all 5 tests)

- [ ] **Step 6: Write the test-plan doc**

Create `docs/test-plan-for-profile-management.md`:

```markdown
# Test Plan: Profile Management

## 測試情境

使用者跨多個 Jenkins 站台工作，透過具名 profile 切換設定，而不必手動複製 `.env` 檔案。

## 測試目標

驗證使用者可以：
1. 列出目前有哪些 profile、哪個是 active
2. 持久切換 active profile，並在下次執行指令時繼續生效
3. 用 `--profile` 做單次覆蓋，不影響持久狀態
4. 在指到不存在的 profile 時得到清楚的錯誤訊息，而不是靜默使用錯的站台

## 涵蓋的指令

| 指令 | 測試目的 | 預期結果 |
|------|---------|---------|
| `profile list` | 列出所有 profile 與目前 active 的是誰 | 顯示 `default` 及所有具名 profile，標出 active |
| `profile use <name>` | 持久切換 active profile | 寫入 `current_profile` 狀態檔，之後的指令都套用 |
| `profile use --default` | 切回預設 `.env` | 清除 `current_profile` 狀態檔 |
| `profile current` | 顯示目前生效的 profile 與其來源 | 顯示 profile 名稱、來源、對應設定檔路徑 |
| `--profile <name>` | 單次覆蓋 | 只影響該次呼叫，不寫入任何狀態檔 |

## 測試前置條件

跟其他測試計畫不同，這裡**不需要**真的 Jenkins server 在跑 -- `profile` 系列指令都只是檔案系統操作。測試透過把 `HOME` 環境變數導向一個暫時目錄來隔離 `~/.jenkins-inspector`，不會碰到開發者本機的真實設定。

## 測試步驟

### 1. 沒有任何 profile 時列出清單

```bash
HOME=/tmp/fake-home jenkee profile list
```

**預期結果**：顯示 `default (active)`，不報錯。

### 2. 建立並切換 profile

```bash
mkdir -p /tmp/fake-home/.jenkins-inspector/profiles
cat > /tmp/fake-home/.jenkins-inspector/profiles/ops.env <<EOF
JENKINS_URL=http://ops.example.com/
JENKINS_USER_ID=u
JENKINS_API_TOKEN=t
EOF
HOME=/tmp/fake-home jenkee profile use ops
HOME=/tmp/fake-home jenkee profile list
```

**預期結果**：`profile use` 顯示切換成功；`profile list` 顯示 `ops (active)`。

### 3. 單次覆蓋不動持久狀態

```bash
HOME=/tmp/fake-home jenkee --profile ops profile current
cat /tmp/fake-home/.jenkins-inspector/current_profile  # 應該還是原本的狀態，沒被 --profile 覆蓋
```

### 4. 指到不存在的 profile

```bash
HOME=/tmp/fake-home jenkee profile use does-not-exist
```

**預期結果**：exit code 1，錯誤訊息包含建立 profile 的操作指引（`mkdir -p ...`）。
```

- [ ] **Step 7: Commit**

```bash
git add jenkins_tools/cli.py tests/test_profile_command_cli.py docs/test-plan-for-profile-management.md
git commit -m "feat: wire --profile flag and profile command into the CLI"
```

---

### Task 5: Documentation and discoverability

**Files:**
- Modify: `jenkins_tools/commands/help.py:14-40` (`COMMAND_DESCRIPTIONS`)
- Modify: `jenkins_tools/commands/prompt.py` (embedded commands listing)
- Modify: `README.md:186-206` (command table)
- Create: `docs/examples/profile.md`
- Test: extend `tests/test_profile_command_cli.py`

**Interfaces:**
- Consumes: the finished `profile` command from Task 4
- Produces: `jenkee help profile` works, `jenkee prompt` mentions `profile`, README lists it

- [ ] **Step 1: Write the failing test**

Append to `tests/test_profile_command_cli.py`:

```python
def test_help_profile_shows_documentation():
    result = subprocess.run(
        ["jenkee", "help", "profile"], capture_output=True, text=True,
    )

    assert result.returncode == 0
    assert "profile" in result.stdout.lower()
    assert "jenkee profile list" in result.stdout
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_profile_command_cli.py::test_help_profile_shows_documentation -v`
Expected: FAIL -- `Error: Unknown command 'profile'` (help.py doesn't know about it yet)

- [ ] **Step 3: Add the entry to `help.py`**

In `jenkins_tools/commands/help.py`, in `COMMAND_DESCRIPTIONS` (currently lines 14-40), add after `"domain"`:

```python
        "domain": "Manage credentials domains",
        "profile": "Manage named Jenkins connection profiles (multi-site support)",
```

- [ ] **Step 4: Create `docs/examples/profile.md`**

```markdown
# profile - 管理多組 Jenkins 連線設定

## 用途

讓 `jenkee` 在多個 Jenkins 站台之間切換，不必手動複製 `.env` 檔案。行為對應 `aws --profile` 的心智模型：預設的 `~/.jenkins-inspector/.env` 永遠是合法的「無 profile」狀態，profile 是疊加上去的加法功能。

## 基本語法

```bash
jks profile list
jks profile use <name>
jks profile use --default
jks profile current
jks --profile <name> <any-command>
```

## 設定解析順序

第一個命中就用：

1. `--profile <name>` -- 單次覆蓋
2. `JENKEE_PROFILE` 環境變數 -- session 範圍覆蓋
3. `~/.jenkins-inspector/current_profile` -- `jenkee profile use <name>` 設定的持久狀態
4. `~/.jenkins-inspector/.env` -- 預設，沒有任何 profile 設定時的既有行為

## 建立 profile

Profile 檔案格式跟 `.env`完全相同，需要手動建立（機密不透過指令參數輸入）：

```bash
mkdir -p ~/.jenkins-inspector/profiles
cat > ~/.jenkins-inspector/profiles/pchome-prod.env <<EOF
JENKINS_URL=http://jenkins.prod.pchome.tenmax.tw/
JENKINS_USER_ID=your_email@example.com
JENKINS_API_TOKEN=your_api_token
EOF
```

## 執行範例

### 列出所有 profile

```bash
$ jks profile list
Available profiles:
  default (active)
  ops
  pchome-prod
```

### 持久切換

```bash
$ jks profile use pchome-prod
✓ Switched to profile 'pchome-prod'
  Using: /Users/you/.jenkins-inspector/profiles/pchome-prod.env

$ jks profile list
Available profiles:
  default
  ops
  pchome-prod (active)
```

### 切回預設

```bash
$ jks profile use --default
✓ Switched to default profile
  Using: /Users/you/.jenkins-inspector/.env
```

### 單次覆蓋（不影響持久狀態）

```bash
$ jks --profile ops list-jobs --all
Active profile: ops (http://ops.example.com/)
...
```

### 查看目前生效的 profile

```bash
$ jks profile current
Profile: pchome-prod
Source: jenkee profile use
Config file: /Users/you/.jenkins-inspector/profiles/pchome-prod.env
Jenkins URL: http://jenkins.prod.pchome.tenmax.tw/
```

### 指到不存在的 profile

```bash
$ jks profile use typo-name
Error: Profile 'typo-name' not found at /Users/you/.jenkins-inspector/profiles/typo-name.env

Create it first:
  mkdir -p /Users/you/.jenkins-inspector/profiles
  cat > /Users/you/.jenkins-inspector/profiles/typo-name.env << 'EOF'
  JENKINS_URL=http://your-jenkins-server:8080/
  JENKINS_USER_ID=your_email@example.com
  JENKINS_API_TOKEN=your_api_token
  EOF
```

## 破壞性指令的安全提示

不論是不是預設 profile，`delete-job`、`delete-builds`、`groovy`、`disable-job`、`enable-job`、`domain create/update/delete`、`gcp credential delete` 在確認前都會先顯示目前作用的站台：

```bash
$ jks delete-job old-job
Active profile: pchome-prod (http://jenkins.prod.pchome.tenmax.tw/)
Are you sure you want to delete job 'old-job'? (y/N):
```

## 注意事項

1. Profile 之間不會互相同步，每台機器要各自建立
2. `profile list` 即使目前的 `current_profile` 狀態檔指到一個已被刪除的 profile，仍然可以正常執行 -- 用它來找出可用的 profile 名稱，再用 `profile use --default` 或 `profile use <name>` 修復
3. `current_profile` 狀態檔或 `--profile`/`JENKEE_PROFILE` 指到不存在的 profile 時，指令會直接報錯中止，不會靜默退回預設站台
```

- [ ] **Step 5: Update `jenkins_tools/commands/prompt.py`'s embedded command list**

In `_show_default_prompt`, in the `Commands:` block, add after the `domain create` line:

```python
  domain create <name>              建立新 domain (需確認)
  profile list                      列出所有已設定的 profile
  profile use <name>                切換目前使用的 profile（持久）
  profile current                   顯示目前生效的 profile
```

- [ ] **Step 6: Update `README.md`'s command table**

In `README.md`, in the general command table (currently lines 186-206), add after the `auth` row:

```markdown
| `auth` | 驗證 Jenkins 認證 | `jenkee auth` |
| `profile` | 管理多組 Jenkins 連線設定（多站台） | `jenkee profile list` / `jenkee profile use <name>` |
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `pytest tests/test_profile_command_cli.py -v`
Expected: PASS (all 6 tests, including the new `test_help_profile_shows_documentation`)

- [ ] **Step 8: Commit**

```bash
git add jenkins_tools/commands/help.py jenkins_tools/commands/prompt.py README.md docs/examples/profile.md tests/test_profile_command_cli.py
git commit -m "docs: document the profile command in help, prompt, and README"
```

---

### Task 6: Full regression verification

**Files:** none (verification only)

**Interfaces:** none -- this task consumes everything from Tasks 1-5 and produces the acceptance evidence the spec explicitly asked for: proof that existing users see zero change.

- [ ] **Step 1: Run the fast test files added in this plan**

Run: `pytest tests/test_jenkins_config_profiles.py tests/test_dangerous_command_profile_banner.py tests/test_profile_command_unit.py tests/test_profile_command_cli.py -v`
Expected: PASS (all tests from Tasks 1-5)

- [ ] **Step 2: Run the full existing suite unmodified**

Run: `pytest -v`
Expected: PASS -- every pre-existing test file (`test_auth.py`, `test_initial_setup.py`, `test_advanced_operations.py`, `test_cleanup_operations.py`, `test_domain_commands.py`, `test_job_organization.py`, `test_gcp_credentials.py`, `test_gcp_freestyle_job.py`, `test_help_flag.py`, `test_list_jobs.py`, `test_pipeline_job_status.py`, `test_prompt.py`, `test_example.py`) passes without any modification. This is the direct evidence for the plan's "existing users see zero change" requirement -- if anything here fails, the regression must be fixed before this task can be checked off, since it's the core compatibility promise of the whole feature.

Note: this run needs Docker (it builds and starts a test Jenkins container per `tests/conftest.py`); if Docker isn't available in the current environment, run at minimum Step 1's fast subset and flag to the user that the docker-dependent suite still needs a run before this task is considered done.

- [ ] **Step 3: Manual smoke test of the exact office-mbp workflow this feature replaces**

```bash
# In a scratch HOME so this never touches real credentials:
export TEST_HOME=$(mktemp -d)
mkdir -p "$TEST_HOME/.jenkins-inspector/profiles"
cat > "$TEST_HOME/.jenkins-inspector/profiles/ops.env" <<EOF
JENKINS_URL=http://ops.example.com/
JENKINS_USER_ID=u
JENKINS_API_TOKEN=t
EOF
cat > "$TEST_HOME/.jenkins-inspector/profiles/pchome-prod.env" <<EOF
JENKINS_URL=http://jenkins.prod.pchome.tenmax.tw/
JENKINS_USER_ID=u
JENKINS_API_TOKEN=t
EOF
HOME="$TEST_HOME" jenkee profile list
HOME="$TEST_HOME" jenkee profile use pchome-prod
HOME="$TEST_HOME" jenkee profile current
HOME="$TEST_HOME" jenkee profile use --default
rm -rf "$TEST_HOME"
```

Expected: `profile list` shows both profiles with `default (active)` initially; after `use pchome-prod`, `profile current` reports `Profile: pchome-prod` and the pchome URL; after `use --default`, the state file is gone. No step prompts for credentials on the command line -- everything came from hand-edited files, matching the "no secrets as CLI args" constraint.

- [ ] **Step 4: Confirm no task in this plan touched version numbers or release tags**

This is intentionally out of scope -- `pyproject.toml` / `jenkins_tools/__init__.py` version bumps and `git tag` pushes trigger the automated PyPI release pipeline (`CODING_GUIDE.md`'s release process), which is a separate, explicit decision for the user to make when they're ready to publish, not an implementation step.
