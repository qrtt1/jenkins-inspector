"""
測試 JenkinsTestInstance.get_env() 是否正確隔離 HOME

背景：get_env() 過去只覆蓋 JENKINS_URL/JENKINS_USER_ID/JENKINS_API_TOKEN，
沒有隔離 HOME。如果開發者本機 ~/.jenkins-inspector/current_profile 剛好指到一個
named profile，jenkee 會讓該 profile 檔案內容蓋過這裡注入的假環境變數
（named profile 的設計本來就該贏過 stray env var），導致測試實際打到真實
Jenkins 而非測試容器。正確做法是把 HOME 也隔離到乾淨的 tmp 目錄。
"""
from pathlib import Path

from conftest import JenkinsTestInstance


class _FakeContainer:
    """假的 DockerContainer，只提供 JenkinsTestInstance.__init__ 需要的介面"""

    def get_container_host_ip(self):
        return "127.0.0.1"

    def get_exposed_port(self, port):
        return 12345


def test_get_env_isolates_home_from_developer_machine(monkeypatch, tmp_path):
    real_home = tmp_path / "real-home"
    (real_home / ".jenkins-inspector").mkdir(parents=True)
    (real_home / ".jenkins-inspector" / "current_profile").write_text("ops\n")
    monkeypatch.setenv("HOME", str(real_home))

    instance = JenkinsTestInstance(_FakeContainer())
    env = instance.get_env()

    assert env["HOME"] != str(real_home)
    isolated_home = Path(env["HOME"])
    assert not (isolated_home / ".jenkins-inspector" / "current_profile").exists()


def test_get_env_still_points_jenkins_vars_at_the_container(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path / "real-home"))

    instance = JenkinsTestInstance(_FakeContainer())
    env = instance.get_env()

    assert env["JENKINS_URL"] == instance.url
    assert env["JENKINS_USER_ID"] == instance.username
    assert env["JENKINS_API_TOKEN"] == instance.token


def test_get_env_forces_a_fixed_named_profile(monkeypatch, tmp_path):
    """就算 HOME 隔離哪天又失效，固定名稱的 profile 也是第二道防線：
    測試斷言的是這個固定名字，不是真的會在使用者機器上出現的名字。"""
    monkeypatch.setenv("HOME", str(tmp_path / "real-home"))

    instance = JenkinsTestInstance(_FakeContainer())
    env = instance.get_env()

    assert env["JENKEE_PROFILE"] == JenkinsTestInstance.TEST_PROFILE_NAME

    profile_path = (
        Path(env["HOME"]) / ".jenkins-inspector" / "profiles" / f"{JenkinsTestInstance.TEST_PROFILE_NAME}.env"
    )
    assert profile_path.exists()
    content = profile_path.read_text()
    assert f"JENKINS_URL={instance.url}" in content
    assert f"JENKINS_USER_ID={instance.username}" in content
    assert f"JENKINS_API_TOKEN={instance.token}" in content


def test_get_bad_auth_env_isolates_home_without_forcing_named_profile(monkeypatch, tmp_path):
    """壞 token 測試不能走 named profile：profile 檔案裡的正確 token 會蓋過
    這裡刻意注入的錯誤 token，讓「必須認證失敗」的測試失去意義。"""
    real_home = tmp_path / "real-home"
    (real_home / ".jenkins-inspector").mkdir(parents=True)
    (real_home / ".jenkins-inspector" / "current_profile").write_text("ops\n")
    monkeypatch.setenv("HOME", str(real_home))

    instance = JenkinsTestInstance(_FakeContainer())
    env = instance.get_bad_auth_env()

    assert env["HOME"] != str(real_home)
    assert "JENKEE_PROFILE" not in env
    assert env["JENKINS_API_TOKEN"] == "intentionally-wrong-token-for-testing"
