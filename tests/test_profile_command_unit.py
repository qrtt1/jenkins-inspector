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
