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
    assert "default (not configured) (active)" in result.stdout


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
    assert "ops (http://ops/) (active)" in list_result.stdout


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
