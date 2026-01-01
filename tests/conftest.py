import base64
import os
import re
import time
import urllib.error
import urllib.request
from http.client import RemoteDisconnected
from pathlib import Path
from typing import Generator

import pytest
from testcontainers.core.container import DockerContainer
from testcontainers.core.wait_strategies import LogMessageWaitStrategy


class JenkinsTestInstance:
    """封裝 Jenkins 測試實例的設定與連線資訊"""

    def __init__(self, container: DockerContainer):
        self.container = container
        host = container.get_container_host_ip()
        port = container.get_exposed_port(8080)
        self.url = f"http://{host}:{port}/"
        self.username = "jenkins-test"
        self.token = "1100000000000000000000000000000000"

    def get_env(self) -> dict:
        """取得包含 Jenkins 連線資訊的環境變數字典"""
        env = os.environ.copy()
        env["JENKINS_URL"] = self.url
        env["JENKINS_USER_ID"] = self.username
        env["JENKINS_API_TOKEN"] = self.token
        return env

    def get_logs(self) -> tuple[str, str]:
        """
        取得 Jenkins container logs

        Returns:
            tuple[str, str]: (stdout, stderr)
        """
        return self.container.get_logs()

    def get_logs_combined(self, mark_streams: bool = False) -> str:
        """
        取得合併的 Jenkins container logs (stdout + stderr)

        Args:
            mark_streams: 是否標示 stdout 和 stderr（預設 False）

        Returns:
            str: 合併的 logs 內容
        """
        stdout, stderr = self.get_logs()
        combined = []

        if stdout:
            stdout_text = stdout.decode('utf-8', errors='ignore') if isinstance(stdout, bytes) else stdout
            if mark_streams and stdout_text.strip():
                combined.append("=== STDOUT ===")
                combined.append(stdout_text)
            elif stdout_text.strip():
                combined.append(stdout_text)

        if stderr:
            stderr_text = stderr.decode('utf-8', errors='ignore') if isinstance(stderr, bytes) else stderr
            if mark_streams and stderr_text.strip():
                combined.append("=== STDERR ===")
                combined.append(stderr_text)
            elif stderr_text.strip():
                combined.append(stderr_text)

        return '\n'.join(combined)

    def assert_no_errors_in_logs(self):
        """確認 logs 中沒有 ERROR 或 Exception"""
        logs = self.get_logs_combined()

        # 檢查是否有真正的錯誤，但允許一些已知的無害訊息
        errors = []
        for line in logs.split('\n'):
            # 跳過已知的無害訊息
            if 'Failed to load' in line and 'init.groovy.d' in line:
                continue  # init scripts 找不到是正常的
            if 'NO JSP Support' in line:
                continue  # JSP 不支援是預期的

            # 檢查真正的錯誤
            if re.search(r'\b(ERROR|SEVERE|Exception)\b', line):
                errors.append(line.strip())

        if errors:
            print("\n=== Found errors in Jenkins logs ===")
            for error in errors[:10]:  # 顯示前 10 個錯誤
                print(error)

        assert not errors, f"Found {len(errors)} errors in Jenkins logs"


def wait_for_jenkins(url: str, username: str, token: str, timeout_seconds: int = 180) -> None:
    """等待 Jenkins 啟動並可以透過 API 認證"""
    auth = base64.b64encode(f"{username}:{token}".encode()).decode()
    req = urllib.request.Request(
        f"{url}whoAmI/api/json", headers={"Authorization": f"Basic {auth}"}
    )
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status == 200:
                    return
        except (
            urllib.error.HTTPError,
            urllib.error.URLError,
            TimeoutError,
            RemoteDisconnected,
            ConnectionResetError,
        ):
            time.sleep(5)
    raise AssertionError("Timed out waiting for Jenkins")


@pytest.fixture(scope="session")
def jenkins_init_dir() -> Path:
    """Jenkins init scripts 目錄路徑"""
    test_dir = Path(__file__).resolve().parent
    return test_dir / "fixtures"


@pytest.fixture(scope="session")
def jenkins_container(jenkins_init_dir: Path) -> Generator[DockerContainer, None, None]:
    """
    啟動 Jenkins container (session scope)

    這個 fixture 在整個測試 session 中只會啟動一次 Jenkins，
    多個測試可以共用同一個 Jenkins instance 以加快測試速度。

    使用自訂 Docker image（從 fixtures/Dockerfile 建立），包含：
    - credentials plugin
    - plain-credentials plugin
    - credentials-binding plugin
    """
    import subprocess

    # 建立自訂的 Jenkins image（包含 credentials plugins）
    dockerfile_path = jenkins_init_dir / "Dockerfile"
    assert dockerfile_path.exists(), f"Dockerfile not found at {dockerfile_path}"

    # 使用 subprocess 建立 image
    build_result = subprocess.run(
        ["docker", "build", "-t", "jenkins-inspector:test", str(jenkins_init_dir)],
        capture_output=True,
        text=True
    )

    assert build_result.returncode == 0, (
        f"Failed to build Jenkins image:\n"
        f"stdout: {build_result.stdout}\n"
        f"stderr: {build_result.stderr}"
    )

    jenkins = DockerContainer("jenkins-inspector:test")
    jenkins.with_env("JAVA_OPTS", "-Djenkins.install.runSetupWizard=false")
    jenkins.with_exposed_ports(8080)
    jenkins.waiting_for(LogMessageWaitStrategy("Jenkins is fully up and running"))
    jenkins.with_volume_mapping(str(jenkins_init_dir), "/usr/share/jenkins/ref/init.groovy.d", mode="ro")

    with jenkins:
        yield jenkins


@pytest.fixture(scope="session")
def jenkins_instance(jenkins_container: DockerContainer) -> Generator[JenkinsTestInstance, None, None]:
    """
    提供已啟動並就緒的 Jenkins 測試實例 (session scope)

    包含 URL、認證資訊和實用方法。
    會確保 Jenkins 啟動過程中沒有錯誤。
    測試結束時會印出 Jenkins logs 的摘要。

    Constraints:
        - Jenkins 必須運行在 localhost/127.0.0.1（安全考量）
    """
    instance = JenkinsTestInstance(jenkins_container)

    # Constraint: 確保 Jenkins 在 localhost
    from urllib.parse import urlparse
    parsed = urlparse(instance.url)
    assert parsed.hostname in ("localhost", "127.0.0.1"), (
        f"Security constraint: Jenkins must run on localhost, got {parsed.hostname}"
    )

    wait_for_jenkins(instance.url, instance.username, instance.token)

    # 確保 Jenkins 啟動過程中沒有錯誤
    instance.assert_no_errors_in_logs()

    yield instance

    # Teardown: 印出完整的 Jenkins logs（標示 stdout/stderr）
    print("\n" + "=" * 80)
    print("Jenkins Container Logs (with stream markers)")
    print("=" * 80)

    # 取得標示 stdout/stderr 的完整 logs
    logs = instance.get_logs_combined(mark_streams=True)
    print(logs)

    print("=" * 80)


@pytest.fixture
def jenkins_env(jenkins_instance: JenkinsTestInstance) -> dict:
    """
    提供包含 Jenkins 連線資訊的環境變數 (function scope)

    適合需要透過環境變數傳遞設定給 subprocess 的測試。
    """
    return jenkins_instance.get_env()


@pytest.fixture
def jenkins_bad_env(jenkins_instance: JenkinsTestInstance) -> dict:
    """
    提供包含錯誤認證的環境變數 (function scope)

    用於測試認證失敗的情況。
    """
    import os
    env = os.environ.copy()
    env["JENKINS_URL"] = jenkins_instance.url
    env["JENKINS_USER_ID"] = jenkins_instance.username
    env["JENKINS_API_TOKEN"] = "intentionally-wrong-token-for-testing"
    return env


class JenkeeCommandBuilder:
    """
    Builder for running jenkee commands with options

    只在需要設定選項時使用，最後呼叫 .run() 執行

    選項：
        .with_timeout(seconds) - 設定執行逾時
        .allow_failure()       - 允許失敗（不做斷言）
        .must_fail()          - 必須失敗（斷言 returncode != 0）
        .with_stdin(input)    - 提供 stdin 輸入
    """

    def __init__(self, jenkins_env: dict, command: str, *args):
        self._jenkins_env = jenkins_env
        self._command = command
        self._args = list(args)
        self._check = True
        self._timeout: int | None = None
        self._stdin_input: str | None = None

    def with_timeout(self, timeout: int) -> "JenkeeCommandBuilder":
        """設定執行逾時（秒）"""
        self._timeout = timeout
        return self

    def allow_failure(self) -> "JenkeeCommandBuilder":
        """允許指令執行失敗（不自動斷言）"""
        self._check = False
        return self

    def must_fail(self) -> "JenkeeCommandBuilder":
        """斷言指令必須失敗（returncode != 0）"""
        self._check = "must_fail"
        return self

    def with_stdin(self, stdin_input: str) -> "JenkeeCommandBuilder":
        """提供 stdin 輸入"""
        self._stdin_input = stdin_input
        return self

    def run(self):
        """執行指令"""
        import subprocess
        from urllib.parse import urlparse

        # Security check: 執行前確認 JENKINS_URL 是 localhost
        jenkins_url = self._jenkins_env.get("JENKINS_URL", "")
        if jenkins_url:
            parsed = urlparse(jenkins_url)
            assert parsed.hostname in ("localhost", "127.0.0.1"), (
                f"Security constraint: JENKINS_URL must be localhost, got {parsed.hostname}"
            )

        cmd = ["jenkee", self._command] + self._args
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            input=self._stdin_input,
            env=self._jenkins_env,
            timeout=self._timeout,
        )

        if self._check is True:
            # 預設行為：斷言成功
            assert result.returncode == 0, f"Command failed: {' '.join(cmd)}\n{result.stderr}"
        elif self._check == "must_fail":
            # must_fail：斷言失敗
            assert result.returncode != 0, f"Command should have failed but succeeded: {' '.join(cmd)}"
        # self._check is False: allow_failure，不做斷言

        return result


class JenkeeRunner:
    """執行 jenkee 指令的入口"""

    def __init__(self, jenkins_env: dict):
        self._jenkins_env = jenkins_env

    def run(self, command: str, *args):
        """
        直接執行指令（最常用）

        Args:
            command: jenkee 子指令
            *args: 命令參數

        Returns:
            subprocess.CompletedProcess

        範例：
            run_jenkee.run("auth")
            run_jenkee.run("list-views", "--format", "json")
        """
        return JenkeeCommandBuilder(self._jenkins_env, command, *args).run()

    def build_command(self, command: str, *args) -> JenkeeCommandBuilder:
        """
        建立命令 builder（需要設定選項時使用）

        Args:
            command: jenkee 子指令
            *args: 命令參數

        Returns:
            JenkeeCommandBuilder - 可串接 with_timeout()、allow_failure() 等選項

        範例：
            run_jenkee.build_command("auth").with_timeout(30).run()
            run_jenkee.build_command("auth").allow_failure().run()
        """
        return JenkeeCommandBuilder(self._jenkins_env, command, *args)


@pytest.fixture
def run_jenkee(jenkins_env) -> JenkeeRunner:
    """
    提供執行 jenkee 指令的 runner (function scope)

    自動帶入正確的 Jenkins 環境變數。

    使用範例：
        # 直接執行（最常用）
        run_jenkee.run("auth")
        result = run_jenkee.run("list-views")

        # 需要 builder 選項時
        run_jenkee.build_command("auth").with_timeout(30).run()
        run_jenkee.build_command("auth").allow_failure().run()
    """
    return JenkeeRunner(jenkins_env)


@pytest.fixture
def run_jenkee_authed(run_jenkee) -> JenkeeRunner:
    """
    提供已驗證 auth 成功的 jenkee runner (function scope)

    在返回 runner 前會先執行 auth 驗證，確保認證正常。
    適合用於其他指令的測試，確保環境可用。

    使用範例：
        # 直接使用，已確認 auth 通過
        result = run_jenkee_authed.run("list-views")
    """
    # 執行 auth 驗證
    auth_result = run_jenkee.run("auth")
    assert auth_result.returncode == 0, "Auth verification failed before test"
    assert "jenkins-test" in auth_result.stdout, "Wrong user authenticated"

    return run_jenkee


@pytest.fixture
def run_jenkee_bad_auth(jenkins_bad_env) -> JenkeeRunner:
    """
    提供執行 jenkee 指令的 runner，使用錯誤的認證 (function scope)

    用於測試認證失敗的情況。

    使用範例：
        # 測試認證失敗
        run_jenkee_bad_auth.build_command("auth").must_fail().run()
    """
    return JenkeeRunner(jenkins_bad_env)


@pytest.fixture(scope="session")
def gcp_key_files() -> dict[str, Path]:
    """
    提供 GCP Service Account key files 路徑 (session scope)

    包含兩組 SA keys，用於測試一般操作和 key rotation。
    這些 keys 應該放在 tests/fixtures/gcp-keys/ 目錄下。

    Returns:
        dict: key file 路徑字典
            - 'sa1': SA-1 的 key file 路徑
            - 'sa2': SA-2 的 key file 路徑

    使用範例：
        def test_create_credential(run_jenkee, gcp_key_files):
            result = run_jenkee.run("gcp", "credential", "create",
                                   "test-cred", str(gcp_key_files['sa1']))

    注意：
        - 這些 key files 不應該提交到版本控制
        - 需要在 .gitignore 中排除 tests/fixtures/gcp-keys/*.json
        - Local 環境：如果 key files 不存在，會跳過相關測試
        - CI 環境：應該透過 GitHub Secrets 設定，缺少時會顯示 warning
    """
    test_dir = Path(__file__).resolve().parent
    gcp_keys_dir = test_dir / "fixtures" / "gcp-keys"

    key_files = {
        'sa1': gcp_keys_dir / "jenkee-tester-viewer-sa-1.json",
        'sa2': gcp_keys_dir / "jenkee-tester-viewer-sa-2.json",
    }

    # 檢查 key files 是否存在
    missing_keys = [name for name, path in key_files.items() if not path.exists()]
    if missing_keys:
        # 在 CI 環境中顯示更明確的訊息
        is_ci = os.getenv('CI') == 'true' or os.getenv('GITHUB_ACTIONS') == 'true'
        if is_ci:
            skip_msg = (
                f"GCP key files not found in CI environment: {missing_keys}. "
                f"Please configure GCP_SA1_KEY and GCP_SA2_KEY secrets. "
                f"See docs/GITHUB_SECRETS_SETUP.md for instructions."
            )
        else:
            skip_msg = (
                f"GCP key files not found: {missing_keys}. "
                f"Download keys using: gcloud iam service-accounts keys create"
            )
        pytest.skip(skip_msg)

    return key_files


@pytest.fixture(scope="session")
def gcp_sa1_info(gcp_key_files) -> dict:
    """
    讀取 SA-1 key 資訊用於測試 (session scope)

    Returns:
        dict: SA-1 的 JSON key 內容
    """
    import json
    with open(gcp_key_files['sa1'], 'r') as f:
        return json.load(f)


@pytest.fixture(scope="session")
def gcp_sa2_info(gcp_key_files) -> dict:
    """
    讀取 SA-2 key 資訊用於測試 (session scope)

    Returns:
        dict: SA-2 的 JSON key 內容
    """
    import json
    with open(gcp_key_files['sa2'], 'r') as f:
        return json.load(f)
