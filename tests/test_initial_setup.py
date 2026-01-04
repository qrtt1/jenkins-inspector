"""
測試 Initial Setup and Environment Exploration 工作流程

這個測試檔案對應 docs/test-plan-for-initial-setup.md，
驗證使用者初次設定並探索 Jenkins 環境的完整流程。

測試涵蓋：
1. Jenkins 認證
2. 列出 views
3. 列出 jobs
4. 列出 credentials
5. 錯誤處理
"""
import re
from dataclasses import dataclass
from typing import Set, List, Dict, Optional


# ============================================================================
# Parser Functions - 將命令輸出解析為可精確比對的資料結構
# ============================================================================

@dataclass
class AuthResult:
    """Auth 命令的解析結果"""
    success: bool
    username: Optional[str]
    raw_output: str


def parse_auth_result(stdout: str, stderr: str, returncode: int) -> AuthResult:
    """
    解析 auth 命令的輸出

    預期格式範例：
    - "Authenticated as: jenkins-test"
    - "✓ Authenticated"
    - 或其他包含使用者名稱的格式
    """
    output = stdout + stderr
    success = returncode == 0

    # 嘗試提取使用者名稱
    username = None
    if success:
        # 嘗試多種可能的格式
        patterns = [
            r'Authenticated as:\s*(\S+)',
            r'User:\s*(\S+)',
            r'jenkins-test',  # 直接匹配使用者名稱
        ]
        for pattern in patterns:
            match = re.search(pattern, output)
            if match:
                username = match.group(1) if match.lastindex else 'jenkins-test'
                break

    return AuthResult(
        success=success,
        username=username,
        raw_output=output
    )


def parse_views_list(stdout: str) -> Set[str]:
    """
    解析 list-views 命令的輸出

    預期格式：每行一個 view 名稱
    例如：
        all
        test-view
        empty-view

    Returns:
        Set[str]: view 名稱的集合
    """
    lines = stdout.strip().split('\n')
    views = set()

    for line in lines:
        line = line.strip()
        if line:  # 跳過空行
            views.add(line)

    return views


def parse_jobs_list(stdout: str) -> Set[str]:
    """
    解析 list-jobs 命令的輸出

    預期格式：每行一個 job 名稱
    例如：
        test-job-1
        test-job-2
        test-job-3

    Returns:
        Set[str]: job 名稱的集合
    """
    lines = stdout.strip().split('\n')
    jobs = set()

    for line in lines:
        line = line.strip()
        # 跳過空行和特殊訊息
        if line and not line.startswith('No jobs found') and not line.startswith('Error'):
            jobs.add(line)

    return jobs


@dataclass
class Credential:
    """單一 credential 的資訊"""
    id: str
    type: str
    scope: Optional[str] = None
    description: Optional[str] = None
    username: Optional[str] = None  # 只適用於 UsernamePassword 類型


@dataclass
class CredentialsDomain:
    """Credentials domain 的資訊"""
    name: str
    credentials: List[Credential]


def parse_credentials_list(stdout: str) -> List[CredentialsDomain]:
    """
    解析 list-credentials 命令的輸出

    預期格式：
        === Domain: (global) ===

        ID: test-credential-1
          Type: UsernamePasswordCredentialsImpl
          Scope: GLOBAL
          Description: Test username/password credential
          Username: test-user

        ID: test-credential-2
          Type: StringCredentialsImpl
          Scope: GLOBAL
          Description: Test secret text credential

    Returns:
        List[CredentialsDomain]: domains 列表，每個包含其 credentials
    """
    domains = []
    current_domain = None
    current_credential = None

    lines = stdout.split('\n')

    for line in lines:
        # Domain header
        domain_match = re.match(r'===\s*Domain:\s*(.+?)\s*===', line)
        if domain_match:
            if current_credential and current_domain:
                current_domain.credentials.append(current_credential)
            if current_domain:
                domains.append(current_domain)
            domain_name = domain_match.group(1)
            current_domain = CredentialsDomain(name=domain_name, credentials=[])
            current_credential = None
            continue

        # Credential ID (開始新的 credential)
        if line.startswith('ID:'):
            if current_credential and current_domain:
                current_domain.credentials.append(current_credential)

            cred_id = line.split(':', 1)[1].strip()
            current_credential = Credential(id=cred_id, type='')
            continue

        # Credential 屬性
        if current_credential:
            if line.strip().startswith('Type:'):
                # 提取簡短的類型名稱
                type_full = line.split(':', 1)[1].strip()
                # 取得類別名稱的最後部分 (例如 UsernamePasswordCredentialsImpl)
                current_credential.type = type_full.split('.')[-1]
            elif line.strip().startswith('Scope:'):
                current_credential.scope = line.split(':', 1)[1].strip()
            elif line.strip().startswith('Description:'):
                current_credential.description = line.split(':', 1)[1].strip()
            elif line.strip().startswith('Username:'):
                current_credential.username = line.split(':', 1)[1].strip()

    # 加入最後一個 credential 和 domain
    if current_credential and current_domain:
        current_domain.credentials.append(current_credential)
    if current_domain:
        domains.append(current_domain)

    return domains


def find_credential_by_id(domains: List[CredentialsDomain], cred_id: str) -> Optional[Credential]:
    """在 domains 中尋找指定 ID 的 credential"""
    for domain in domains:
        for cred in domain.credentials:
            if cred.id == cred_id:
                return cred
    return None


# ============================================================================
# 測試函數
# ============================================================================

def test_step1_verify_jenkins_authentication(run_jenkee_authed):
    """
    測試步驟 1: 驗證 Jenkins 認證

    預期結果：
    - Exit code: 0
    - 顯示認證成功訊息
    - 顯示正確的使用者名稱
    """
    # Act: 執行 auth 指令
    result = run_jenkee_authed.run("auth")

    # Parse: 解析輸出
    auth_result = parse_auth_result(result.stdout, result.stderr, result.returncode)

    # Assert: 驗證認證成功
    assert auth_result.success, "Authentication should succeed"
    assert auth_result.username is not None, "Should extract username from output"
    assert auth_result.username == "jenkins-test", \
        f"Expected username 'jenkins-test', got '{auth_result.username}'"


def test_step2_list_all_views(run_jenkee_authed):
    """
    測試步驟 2: 列出所有 Views

    預期結果：
    - Exit code: 0
    - 至少包含 "all" view (注意是小寫)
    - 包含測試用的自訂 views
    """
    # Act: 執行 list-views 指令
    result = run_jenkee_authed.run("list-views")

    # Parse: 解析 views 列表
    views = parse_views_list(result.stdout)

    # Assert: 驗證包含預期的 views
    expected_views = {"all", "test-view", "empty-view"}
    assert expected_views.issubset(views), \
        f"Expected views {expected_views}, but got {views}"


def test_step3_list_all_jobs(run_jenkee_authed):
    """
    測試步驟 3: 列出所有 Jobs (使用 --all)

    預期結果：
    - Exit code: 0
    - 顯示所有測試 jobs
    """
    # Act: 執行 list-jobs --all 指令
    result = run_jenkee_authed.run("list-jobs", "--all")

    # Parse: 解析 jobs 列表
    jobs = parse_jobs_list(result.stdout)

    # Assert: 驗證包含所有測試 jobs
    expected_jobs = {"test-job-1", "test-job-2", "test-job-3"}
    assert expected_jobs.issubset(jobs), \
        f"Expected jobs {expected_jobs}, but got {jobs}"


def test_step4_list_jobs_in_specific_view(run_jenkee_authed):
    """
    測試步驟 4: 列出特定 View 的 Jobs

    預期結果：
    - Exit code: 0
    - 只顯示該 view 中的 jobs
    - test-view 應包含 test-job-1 和 test-job-2
    """
    # Act: 執行 list-jobs test-view 指令
    result = run_jenkee_authed.run("list-jobs", "test-view")

    # Parse: 解析 jobs 列表
    jobs = parse_jobs_list(result.stdout)

    # Assert: 驗證精確的 job 列表
    expected_jobs = {"test-job-1", "test-job-2"}
    assert jobs == expected_jobs, \
        f"Expected exactly {expected_jobs}, but got {jobs}"


def test_step5_list_credentials(run_jenkee_authed):
    """
    測試步驟 5: 列出所有 Credentials

    預期結果：
    - Exit code: 0
    - 顯示 credentials metadata
    - 不洩漏 secret 內容
    - 包含測試用的 credentials

    注意：需要安裝 credentials plugin（已透過自訂 Docker image 安裝）
    """
    # Act: 執行 list-credentials 指令
    result = run_jenkee_authed.run("list-credentials")

    # Parse: 解析 credentials 列表
    domains = parse_credentials_list(result.stdout)

    # Assert: 驗證有 domain
    assert len(domains) > 0, "Should have at least one domain"

    # 驗證包含測試 credentials
    cred1 = find_credential_by_id(domains, "test-credential-1")
    assert cred1 is not None, "Should contain test-credential-1"
    assert cred1.type == "UsernamePasswordCredentialsImpl", \
        f"test-credential-1 should be UsernamePasswordCredentialsImpl, got {cred1.type}"
    assert cred1.username == "test-user", \
        f"test-credential-1 username should be 'test-user', got {cred1.username}"

    cred2 = find_credential_by_id(domains, "test-credential-2")
    assert cred2 is not None, "Should contain test-credential-2"
    assert cred2.type == "StringCredentialsImpl", \
        f"test-credential-2 should be StringCredentialsImpl, got {cred2.type}"

    cred3 = find_credential_by_id(domains, "test-credential-3")
    assert cred3 is not None, "Should contain test-credential-3"

    # 驗證不洩漏 secret（不應該包含實際密碼或 secret 值）
    output_lower = result.stdout.lower()
    assert "test-password" not in output_lower, "Should not leak password values"
    assert "test-secret-value" not in output_lower, "Should not leak secret values"


def test_complete_workflow(run_jenkee_authed):
    """
    測試完整工作流程：按順序執行所有步驟

    這模擬使用者第一次使用工具探索 Jenkins 環境的真實情境
    """
    # 1. 驗證連線
    auth_result = run_jenkee_authed.run("auth")
    parsed_auth = parse_auth_result(auth_result.stdout, auth_result.stderr, auth_result.returncode)
    assert parsed_auth.success, "Step 1: Authentication failed"

    # 2. 探索 views
    views_result = run_jenkee_authed.run("list-views")
    views = parse_views_list(views_result.stdout)
    expected_views = {"all", "test-view", "empty-view"}
    assert expected_views == views, \
        f"Step 2: Expected exactly {expected_views}, got {views}"

    # 3. 探索所有 jobs
    all_jobs_result = run_jenkee_authed.run("list-jobs", "--all")
    all_jobs = parse_jobs_list(all_jobs_result.stdout)
    expected_jobs = {"test-job-1", "test-job-2", "test-job-3", "long-running-job"}
    assert expected_jobs == all_jobs, \
        f"Step 3: Expected exactly {expected_jobs}, got {all_jobs}"

    # 4. 探索特定 view 的 jobs
    view_jobs_result = run_jenkee_authed.run("list-jobs", "test-view")
    view_jobs = parse_jobs_list(view_jobs_result.stdout)
    assert view_jobs == {"test-job-1", "test-job-2"}, \
        f"Step 4: Expected test-view to contain test-job-1 and test-job-2, got {view_jobs}"

    # 5. 查看 credentials
    creds_result = run_jenkee_authed.run("list-credentials")
    domains = parse_credentials_list(creds_result.stdout)
    assert len(domains) >= 1, f"Step 5: Should have at least 1 domain, got {len(domains)}"

    global_domain = next((d for d in domains if d.name == "(global)"), None)
    assert global_domain is not None, "Step 5: Should include global domain"

    # 驗證恰好有 3 個測試 credentials
    total_creds = sum(len(d.credentials) for d in domains)
    assert total_creds >= 3, f"Step 5: Should have at least 3 credentials, got {total_creds}"

    required_creds = {"test-credential-1", "test-credential-2", "test-credential-3"}
    listed_creds = {cred.id for domain in domains for cred in domain.credentials}
    assert required_creds.issubset(listed_creds), \
        f"Step 5: Missing credentials {required_creds - listed_creds}"


# ============================================================================
# 錯誤情境測試
# ============================================================================

def test_error_wrong_credentials(jenkins_instance):
    """
    錯誤情境：使用錯誤的認證資訊

    預期結果：
    - Exit code: 非 0
    - 顯示認證失敗錯誤訊息
    """
    import subprocess
    import os

    # Arrange: 建立錯誤的環境變數
    env = os.environ.copy()
    env["JENKINS_URL"] = jenkins_instance.url
    env["JENKINS_USER_ID"] = jenkins_instance.username
    env["JENKINS_API_TOKEN"] = "wrong_token_value"

    # Act: 使用錯誤的 token 執行 auth
    result = subprocess.run(
        ["jenkee", "auth"],
        capture_output=True,
        text=True,
        env=env,
    )

    # Parse & Assert: 驗證認證失敗
    auth_result = parse_auth_result(result.stdout, result.stderr, result.returncode)
    assert not auth_result.success, "Should fail with wrong credentials"
    assert len(auth_result.raw_output) > 0, "Should have error message in output"


def test_error_list_jobs_nonexistent_view(run_jenkee_authed):
    """
    錯誤情境：查詢不存在的 View

    預期結果：
    - Exit code: 非 0
    - 顯示 view 不存在的錯誤訊息
    """
    # Act: 嘗試列出不存在的 view 的 jobs
    result = run_jenkee_authed.build_command("list-jobs", "NonExistentView") \
        .allow_failure() \
        .run()

    # Assert: 驗證操作失敗
    assert result.returncode != 0, "Should fail for non-existent view"

    # 驗證有錯誤訊息
    error_output = (result.stderr + result.stdout).lower()
    error_keywords = ["error", "not found", "doesn't exist", "does not exist"]
    has_error_keyword = any(keyword in error_output for keyword in error_keywords)
    assert has_error_keyword, \
        f"Error message should contain one of {error_keywords}, got: {error_output[:100]}"


def test_idempotent_operations(run_jenkee_authed):
    """
    測試冪等性：重複執行 read-only 操作應該都成功且結果一致

    所有 initial setup 中的操作都是 read-only，可以安全地重複執行
    """
    # 記錄第一次的結果
    first_views = None
    first_jobs = None
    first_creds_count = None

    # 重複執行 3 次，驗證每次都成功且結果一致
    for i in range(3):
        # list-views
        views_result = run_jenkee_authed.run("list-views")
        views = parse_views_list(views_result.stdout)

        if i == 0:
            first_views = views
        else:
            assert views == first_views, \
                f"Iteration {i+1}: views changed. Expected {first_views}, got {views}"

        # list-jobs
        jobs_result = run_jenkee_authed.run("list-jobs", "--all")
        jobs = parse_jobs_list(jobs_result.stdout)

        if i == 0:
            first_jobs = jobs
        else:
            assert jobs == first_jobs, \
                f"Iteration {i+1}: jobs changed. Expected {first_jobs}, got {jobs}"

        # list-credentials
        creds_result = run_jenkee_authed.run("list-credentials")
        domains = parse_credentials_list(creds_result.stdout)
        creds_count = sum(len(d.credentials) for d in domains)

        if i == 0:
            first_creds_count = creds_count
        else:
            assert creds_count == first_creds_count, \
                f"Iteration {i+1}: credentials count changed. Expected {first_creds_count}, got {creds_count}"


def test_output_format_clarity(run_jenkee_authed):
    """
    測試輸出格式清晰度

    驗證所有命令的輸出都是清晰易讀的
    """
    # list-views: 應該是簡單的列表（每行一個 view）
    views_result = run_jenkee_authed.run("list-views")
    views = parse_views_list(views_result.stdout)
    expected_views = {"all", "test-view", "empty-view"}
    assert views == expected_views, \
        f"list-views should return exactly {expected_views}, got {views}"

    # 驗證每個 view 名稱都是單一詞彙（不含空格或複雜格式）
    for view in views:
        assert ' ' not in view or view.count(' ') <= 1, \
            f"View name '{view}' should be simple (max 1 space)"

    # list-jobs: 應該是簡單的列表（每行一個 job）
    jobs_result = run_jenkee_authed.run("list-jobs", "--all")
    jobs = parse_jobs_list(jobs_result.stdout)
    expected_jobs = {"test-job-1", "test-job-2", "test-job-3", "long-running-job"}
    assert jobs == expected_jobs, \
        f"list-jobs should return exactly {expected_jobs}, got {jobs}"

    # 驗證每個 job 名稱都是單一詞彙
    for job in jobs:
        assert ' ' not in job or job.count(' ') <= 1, \
            f"Job name '{job}' should be simple (max 1 space)"

    # list-credentials: 應該有結構化的輸出
    creds_result = run_jenkee_authed.run("list-credentials")
    domains = parse_credentials_list(creds_result.stdout)
    assert len(domains) >= 1, \
        f"list-credentials should return at least 1 domain, got {len(domains)}"

    assert any(domain.name == "(global)" for domain in domains), \
        "list-credentials should include global domain"

    # 驗證 domain 中有恰好 3 個 credentials
    total_creds = sum(len(d.credentials) for d in domains)
    assert total_creds >= 3, \
        f"Should have at least 3 credentials, got {total_creds}"

    # 驗證每個 credential 都有必要的欄位
    for domain in domains:
        for cred in domain.credentials:
            assert cred.id, "Credential should have ID"
            assert cred.type, "Credential should have Type"
