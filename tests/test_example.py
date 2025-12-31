"""範例測試：示範如何使用 Jenkins fixtures"""

import subprocess
import urllib.request


def test_jenkins_whoami_api(jenkins_instance):
    """範例：直接使用 Jenkins REST API"""
    import base64

    auth = base64.b64encode(f"{jenkins_instance.username}:{jenkins_instance.token}".encode()).decode()
    req = urllib.request.Request(
        f"{jenkins_instance.url}whoAmI/api/json",
        headers={"Authorization": f"Basic {auth}"}
    )

    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200


def test_jenkee_simple_command(run_jenkee):
    """範例：最簡單的方式 - 直接執行"""
    run_jenkee.run("auth")


def test_jenkee_with_output_check(run_jenkee):
    """範例：檢查指令輸出"""
    result = run_jenkee.run("auth")
    assert result.returncode == 0
    assert result.stdout


def test_with_authed_runner(run_jenkee_authed):
    """範例：使用已驗證 auth 的 runner 測試其他指令"""
    # Arrange: run_jenkee_authed 已經驗證過 auth 通過
    # 註：這個 fixture 會在測試前先執行 auth 驗證

    # Act: 直接執行其他指令，無需再驗證 auth
    result = run_jenkee_authed.run("list-views")

    # Assert: 驗證指令有執行（可能成功或失敗都可以）
    # 重點是 auth 已經被預先驗證了
    assert result is not None


def test_jenkee_with_command_args(run_jenkee):
    """範例：執行帶參數的指令"""
    result = run_jenkee.run("list-views", "--format", "json")
    assert result.returncode == 0


def test_jenkee_with_timeout(run_jenkee):
    """範例：使用 builder 設定 timeout"""
    run_jenkee.build_command("auth").with_timeout(30).run()


def test_jenkee_allow_failure(run_jenkee):
    """範例：使用 builder 允許失敗"""
    result = run_jenkee.build_command("auth").allow_failure().run()
    assert result.returncode == 0


def test_jenkee_builder_chain(run_jenkee):
    """範例：builder 串接多個選項"""
    result = run_jenkee.build_command("auth").with_timeout(30).allow_failure().run()
    assert result.returncode == 0


def test_jenkee_must_fail_with_bad_auth(run_jenkee_bad_auth):
    """範例：使用 must_fail() 測試認證失敗"""
    # 使用錯誤的認證，auth 指令必須失敗
    # must_fail() 會自動斷言 returncode != 0
    result = run_jenkee_bad_auth.build_command("auth").must_fail().run()
    assert result.returncode != 0


def test_jenkee_must_fail_with_invalid_command(run_jenkee):
    """範例：使用 must_fail() 測試不存在的指令"""
    # 使用不存在的指令，必須失敗
    # must_fail() 會自動斷言 returncode != 0
    result = run_jenkee.build_command("non-existent-command").must_fail().run()
    assert result.returncode != 0


def test_jenkee_with_subprocess_directly(jenkins_env):
    """範例：需要完全控制 subprocess 時使用 jenkins_env"""
    result = subprocess.run(
        ["jenkee", "auth"],
        capture_output=True,
        text=True,
        env=jenkins_env,
        timeout=10
    )
    assert result.returncode == 0


def test_jenkins_logs_check(jenkins_instance):
    """範例：檢查 Jenkins container logs"""
    # get_logs() 回傳 (stdout, stderr) tuple
    # 使用 get_logs_combined() 取得合併的 logs
    logs = jenkins_instance.get_logs_combined()
    assert "Jenkins is fully up and running" in logs
