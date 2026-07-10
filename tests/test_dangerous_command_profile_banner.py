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
