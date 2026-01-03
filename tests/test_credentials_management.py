"""
測試 Credentials Management 相關指令

涵蓋指令：
- list-credentials: 列出所有 credentials metadata
- describe-credentials: 查看特定 credential 詳細資訊

測試重點：
- 驗證不洩漏 secrets（在沒有 --show-secret 參數時）
- 測試不同類型的 credentials
- 結構化輸出解析
- Read-only 操作，安全性高
"""
import re
from dataclasses import dataclass
from typing import List, Optional


# ============================================================================
# Parser Functions - 將命令輸出解析為可精確比對的資料結構
# ============================================================================


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

        # Credential 屬性（以 2+ 空白開頭）
        if current_credential and line.startswith('  '):
            line = line.strip()
            if ':' in line:
                key, value = line.split(':', 1)
                value = value.strip()

                if key == 'Type':
                    current_credential.type = value
                elif key == 'Scope':
                    current_credential.scope = value
                elif key == 'Description':
                    current_credential.description = value
                elif key == 'Username':
                    current_credential.username = value

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


@dataclass
class CredentialDetail:
    """Credential 詳細資訊（來自 describe-credentials）"""
    id: str
    type: str
    scope: str
    description: str
    domain: str
    # 可選的額外欄位
    username: Optional[str] = None
    # 安全性檢查：不應該包含實際的 secrets
    has_password: bool = False  # 僅標記是否有 password 欄位，但不儲存值
    has_secret: bool = False    # 僅標記是否有 secret 欄位，但不儲存值


def parse_credential_detail(stdout: str) -> CredentialDetail:
    """
    解析 describe-credentials 命令的輸出

    預期格式：
        === Domain: (global) ===

        ID: test-credential-1
        Type: UsernamePasswordCredentialsImpl
        Scope: GLOBAL
        Description: Test username/password credential

        Details:
          Username: test-user
          Password: ******** (hidden)

    Returns:
        CredentialDetail: credential 詳細資訊
    """
    lines = stdout.split('\n')

    cred_id = None
    cred_type = None
    scope = None
    description = None
    domain = None
    username = None
    has_password = False
    has_secret = False

    for line in lines:
        line = line.strip()

        # Domain header
        domain_match = re.match(r'===\s*Domain:\s*(.+?)\s*===', line)
        if domain_match:
            domain = domain_match.group(1)
            continue

        # 主要欄位
        if line.startswith('ID:'):
            cred_id = line.split(':', 1)[1].strip()
        elif line.startswith('Type:'):
            cred_type = line.split(':', 1)[1].strip()
        elif line.startswith('Scope:'):
            scope = line.split(':', 1)[1].strip()
        elif line.startswith('Description:'):
            description = line.split(':', 1)[1].strip()
        elif line.startswith('Username:'):
            username = line.split(':', 1)[1].strip()
        elif 'Password:' in line or 'password' in line.lower():
            # 檢查是否提到 password（但不擷取值）
            has_password = True
        elif 'Secret:' in line or 'secret' in line.lower():
            # 檢查是否提到 secret（但不擷取值）
            has_secret = True

    if not cred_id or not cred_type:
        raise ValueError("Failed to parse credential detail: missing required fields")

    return CredentialDetail(
        id=cred_id,
        type=cred_type,
        scope=scope or "UNKNOWN",
        description=description or "(no description)",
        domain=domain or "(unknown)",
        username=username,
        has_password=has_password,
        has_secret=has_secret
    )


# ============================================================================
# 測試函數 - List-Credentials 指令
# ============================================================================


def test_list_credentials_basic(run_jenkee_authed):
    """
    測試列出所有 Credentials

    對應 test plan 步驟 1
    """
    # Act: 執行 list-credentials 指令
    result = run_jenkee_authed.run("list-credentials")

    # Parse: 解析 credentials 列表
    domains = parse_credentials_list(result.stdout)

    # Assert: 驗證執行成功
    assert result.returncode == 0, f"list-credentials should succeed, got: {result.stderr}"
    assert len(domains) > 0, "Should have at least one domain"

    # 驗證包含測試 credentials
    cred1 = find_credential_by_id(domains, "test-credential-1")
    assert cred1 is not None, "Should contain test-credential-1"
    assert cred1.type == "UsernamePasswordCredentialsImpl", \
        f"test-credential-1 should be UsernamePasswordCredentialsImpl, got {cred1.type}"

    cred2 = find_credential_by_id(domains, "test-credential-2")
    assert cred2 is not None, "Should contain test-credential-2"
    assert cred2.type == "StringCredentialsImpl", \
        f"test-credential-2 should be StringCredentialsImpl, got {cred2.type}"

    cred3 = find_credential_by_id(domains, "test-credential-3")
    assert cred3 is not None, "Should contain test-credential-3"
    assert cred3.type == "UsernamePasswordCredentialsImpl", \
        f"test-credential-3 should be UsernamePasswordCredentialsImpl, got {cred3.type}"


def test_list_credentials_no_secrets_leaked(run_jenkee_authed):
    """
    測試 list-credentials 不洩漏 Secrets

    對應 test plan 步驟 2
    驗證輸出中不包含實際的 passwords, tokens, private keys
    """
    # Act: 執行 list-credentials 指令
    result = run_jenkee_authed.run("list-credentials")

    # Assert: 驗證不洩漏 secrets
    output = result.stdout.lower()

    # 不應該包含測試用的實際 secrets
    assert "test-password" not in output, \
        "Should not leak test-password"
    assert "admin-password" not in output, \
        "Should not leak admin-password"
    assert "test-secret-value" not in output, \
        "Should not leak test-secret-value"

    # 不應該有 "password=" 或 "secret=" 格式的洩漏
    assert re.search(r'password\s*=\s*\S+', output) is None, \
        "Should not have 'password=<value>' format"
    assert re.search(r'secret\s*=\s*\S+', output) is None, \
        "Should not have 'secret=<value>' format"
    assert re.search(r'token\s*=\s*\S+', output) is None, \
        "Should not have 'token=<value>' format"

    # 可以顯示 username（這不是 secret）
    # 但不應該同時顯示 password


def test_list_credentials_shows_metadata(run_jenkee_authed):
    """
    測試 list-credentials 顯示完整 Metadata

    驗證輸出包含必要的 metadata 欄位
    """
    # Act: 執行 list-credentials 指令
    result = run_jenkee_authed.run("list-credentials")

    # Parse: 解析 credentials 列表
    domains = parse_credentials_list(result.stdout)

    # Assert: 驗證每個 credential 都有必要的 metadata
    for domain in domains:
        for cred in domain.credentials:
            # 必要欄位
            assert cred.id, f"Credential should have ID"
            assert cred.type, f"Credential {cred.id} should have Type"
            assert cred.scope, f"Credential {cred.id} should have Scope"

            # Username 應該顯示（如果有的話）
            if cred.type == "UsernamePasswordCredentialsImpl":
                # UsernamePassword 類型應該有 username
                assert cred.username is not None, \
                    f"UsernamePassword credential {cred.id} should have username"


def test_list_credentials_multiple_types(run_jenkee_authed):
    """
    測試 list-credentials 正確處理不同類型的 Credentials

    對應 test plan 步驟 4
    """
    # Act: 執行 list-credentials 指令
    result = run_jenkee_authed.run("list-credentials")

    # Parse: 解析 credentials 列表
    domains = parse_credentials_list(result.stdout)

    # Assert: 驗證包含不同類型的 credentials
    all_creds = []
    for domain in domains:
        all_creds.extend(domain.credentials)

    # 取得所有類型
    types = {cred.type for cred in all_creds}

    # 應該至少有兩種類型
    assert len(types) >= 2, \
        f"Should have multiple credential types, got: {types}"

    # 應該包含測試用的兩種類型
    assert "UsernamePasswordCredentialsImpl" in types, \
        "Should have UsernamePasswordCredentialsImpl"
    assert "StringCredentialsImpl" in types, \
        "Should have StringCredentialsImpl"


# ============================================================================
# 測試函數 - Describe-Credentials 指令
# ============================================================================


def test_describe_credentials_basic(run_jenkee_authed):
    """
    測試查看特定 Credential 的詳細資訊

    對應 test plan 步驟 3
    """
    # Act: 執行 describe-credentials 指令
    result = run_jenkee_authed.run("describe-credentials", "test-credential-1")

    # Parse: 解析 credential 詳細資訊
    detail = parse_credential_detail(result.stdout)

    # Assert: 驗證執行成功
    assert result.returncode == 0, f"describe-credentials should succeed"
    assert detail.id == "test-credential-1", \
        f"Should describe test-credential-1, got {detail.id}"
    assert detail.type == "UsernamePasswordCredentialsImpl", \
        f"Should have correct type, got {detail.type}"


def test_describe_credentials_no_secrets_without_flag(run_jenkee_authed):
    """
    測試 describe-credentials 在沒有 --show-secret 時不洩漏 Secrets

    這是安全性的關鍵測試
    """
    # Act: 執行 describe-credentials 指令（不帶 --show-secret）
    result = run_jenkee_authed.run("describe-credentials", "test-credential-1")

    # Assert: 驗證不洩漏 secrets
    output = result.stdout.lower()

    # 不應該包含實際的 password
    assert "test-password" not in output, \
        "Should not leak test-password without --show-secret flag"

    # 測試 secret text credential
    result2 = run_jenkee_authed.run("describe-credentials", "test-credential-2")
    output2 = result2.stdout.lower()

    assert "test-secret-value" not in output2, \
        "Should not leak test-secret-value without --show-secret flag"


def test_describe_credentials_shows_username(run_jenkee_authed):
    """
    測試 describe-credentials 顯示 Username（非敏感資訊）

    Username 不是 secret，應該正常顯示
    """
    # Act: 執行 describe-credentials 指令
    result = run_jenkee_authed.run("describe-credentials", "test-credential-1")

    # Parse: 解析 credential 詳細資訊
    detail = parse_credential_detail(result.stdout)

    # Assert: 驗證顯示 username
    assert detail.username is not None, "Should show username"
    assert detail.username == "test-user", \
        f"Should show correct username, got {detail.username}"


def test_describe_credentials_different_types(run_jenkee_authed):
    """
    測試 describe-credentials 處理不同類型的 Credentials

    對應 test plan 步驟 4
    """
    # Test 1: UsernamePassword credential
    result1 = run_jenkee_authed.run("describe-credentials", "test-credential-1")
    detail1 = parse_credential_detail(result1.stdout)

    assert result1.returncode == 0, "Should succeed for UsernamePassword credential"
    assert detail1.type == "UsernamePasswordCredentialsImpl"
    assert detail1.username == "test-user"

    # Test 2: Secret text credential
    result2 = run_jenkee_authed.run("describe-credentials", "test-credential-2")
    detail2 = parse_credential_detail(result2.stdout)

    assert result2.returncode == 0, "Should succeed for StringCredentials"
    assert detail2.type == "StringCredentialsImpl"

    # Test 3: Another UsernamePassword credential
    result3 = run_jenkee_authed.run("describe-credentials", "test-credential-3")
    detail3 = parse_credential_detail(result3.stdout)

    assert result3.returncode == 0, "Should succeed for another UsernamePassword credential"
    assert detail3.type == "UsernamePasswordCredentialsImpl"
    assert detail3.username == "admin-user"


def test_describe_credentials_nonexistent(run_jenkee_authed):
    """
    測試查詢不存在的 Credential

    對應 test plan 錯誤情境測試
    """
    # Act: 執行 describe-credentials 指令（使用不存在的 ID）
    result = run_jenkee_authed.build_command(
        "describe-credentials", "non-existent-credential-id"
    ).allow_failure().run()

    # Assert: 驗證失敗
    assert result.returncode != 0, "Should fail for non-existent credential"
    error_output = (result.stdout + result.stderr).lower()
    assert 'error' in error_output or 'not found' in error_output, \
        f"Should have error message, got: {result.stdout + result.stderr}"


# ============================================================================
# 整合測試 - 完整工作流程
# ============================================================================


def test_complete_credentials_workflow(run_jenkee_authed):
    """
    測試完整的 credentials 查詢工作流程

    對應 test plan 場景 A：驗證環境 Credentials 設定
    """
    # 1. 列出所有 credentials
    list_result = run_jenkee_authed.run("list-credentials")
    domains = parse_credentials_list(list_result.stdout)

    assert list_result.returncode == 0, "Step 1: list-credentials should succeed"
    assert len(domains) > 0, "Step 1: Should have at least one domain"

    # 2. 檢查必要的 credentials 是否存在
    required_creds = ["test-credential-1", "test-credential-2", "test-credential-3"]

    for cred_id in required_creds:
        cred = find_credential_by_id(domains, cred_id)
        assert cred is not None, f"Step 2: {cred_id} should exist"

    # 3. 查看詳細資訊確認設定
    for cred_id in required_creds:
        desc_result = run_jenkee_authed.run("describe-credentials", cred_id)
        assert desc_result.returncode == 0, \
            f"Step 3: describe-credentials should succeed for {cred_id}"

        detail = parse_credential_detail(desc_result.stdout)
        assert detail.id == cred_id, \
            f"Step 3: Should describe {cred_id}, got {detail.id}"

    # 4. 驗證整個流程沒有洩漏 secrets
    all_output = list_result.stdout
    for cred_id in required_creds:
        desc_result = run_jenkee_authed.run("describe-credentials", cred_id)
        all_output += desc_result.stdout

    output_lower = all_output.lower()
    assert "test-password" not in output_lower, \
        "Step 4: Should not leak test-password in any output"
    assert "admin-password" not in output_lower, \
        "Step 4: Should not leak admin-password in any output"
    assert "test-secret-value" not in output_lower, \
        "Step 4: Should not leak test-secret-value in any output"


def test_credentials_output_is_parseable(run_jenkee_authed):
    """
    測試 credentials 指令的輸出可以被腳本解析

    確保輸出格式穩定，適合自動化使用
    """
    # Test list-credentials
    list_result = run_jenkee_authed.run("list-credentials")
    domains = parse_credentials_list(list_result.stdout)

    # 應該能夠成功解析
    assert len(domains) > 0, "Should be able to parse list-credentials output"

    # 每個 credential 應該有必要的欄位
    for domain in domains:
        for cred in domain.credentials:
            assert cred.id, "Parsed credential should have ID"
            assert cred.type, "Parsed credential should have Type"

    # Test describe-credentials
    desc_result = run_jenkee_authed.run("describe-credentials", "test-credential-1")
    detail = parse_credential_detail(desc_result.stdout)

    # 應該能夠成功解析
    assert detail.id == "test-credential-1", "Should be able to parse describe-credentials output"
    assert detail.type, "Parsed detail should have Type"
