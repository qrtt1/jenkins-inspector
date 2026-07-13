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


def test_named_profile_overrides_stale_process_env_vars(tmp_path, monkeypatch):
    """已 export 的 JENKINS_URL 等變數不該蓋掉明確選定的 named profile 內容。"""
    _write_profile(tmp_path, "ops", "http://ops/")
    (tmp_path / "current_profile").write_text("ops\n")
    monkeypatch.setenv("JENKINS_URL", "http://stale-shell-export/")
    monkeypatch.setenv("JENKINS_USER_ID", "stale-user")
    monkeypatch.setenv("JENKINS_API_TOKEN", "stale-token")

    config = JenkinsConfig(base_dir=tmp_path)

    assert config.profile_name == "ops"
    assert config.jenkins_url == "http://ops/"
    assert config.username == "u"
    assert config.api_token == "t"


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


def test_current_profile_as_directory_exits_with_clear_error(tmp_path, capsys):
    (tmp_path / "current_profile").mkdir()

    with pytest.raises(SystemExit) as exc_info:
        JenkinsConfig(base_dir=tmp_path)

    assert exc_info.value.code == 1
    err = capsys.readouterr().err
    assert "current_profile" in err
    assert "profile use --default" in err


def test_current_profile_with_bad_encoding_exits_with_clear_error(tmp_path, capsys):
    (tmp_path / "current_profile").write_bytes(b"\xff\xfe\x00broken")

    with pytest.raises(SystemExit) as exc_info:
        JenkinsConfig(base_dir=tmp_path)

    assert exc_info.value.code == 1
    err = capsys.readouterr().err
    assert "current_profile" in err
    assert "profile use --default" in err


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
