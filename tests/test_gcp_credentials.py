"""
Tests for GCP credentials management using new subcommand structure

These tests use gcp_key_files fixture which provides two SA key files:
- SA-1: jenkee-tester-viewer-sa-1@twjug-lite.iam.gserviceaccount.com
- SA-2: jenkee-tester-viewer-sa-2@twjug-lite.iam.gserviceaccount.com

Tests will be skipped if key files are not found in tests/fixtures/gcp-keys/

Usage:
    # Download keys first (one-time setup):
    mkdir -p tests/fixtures/gcp-keys
    gcloud iam service-accounts keys create tests/fixtures/gcp-keys/jenkee-tester-viewer-sa-1.json \
        --iam-account=jenkee-tester-viewer-sa-1@twjug-lite.iam.gserviceaccount.com
    gcloud iam service-accounts keys create tests/fixtures/gcp-keys/jenkee-tester-viewer-sa-2.json \
        --iam-account=jenkee-tester-viewer-sa-2@twjug-lite.iam.gserviceaccount.com

    # Run tests:
    pytest tests/test_gcp_credentials.py -v
"""

import json
import pytest
from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path


# ============================================================================
# Data Structures
# ============================================================================

@dataclass
class GCPCredential:
    """GCP credential 的結構化資料"""
    id: str
    type: str
    file_name: Optional[str] = None
    description: Optional[str] = None
    project_id: Optional[str] = None


# ============================================================================
# Parser Functions - 將命令輸出解析為可精確比對的資料結構
# ============================================================================

def parse_gcp_credential_list(stdout: str) -> List[GCPCredential]:
    """
    解析 gcp credential list 命令的輸出

    預期格式：
        GCP Service Account Credentials:

        ID: my-gcp-sa
          Type: GoogleRobotPrivateKeyCredentials
          Project ID: my-gcp-sa

        ID: another-gcp-sa
          Type: GoogleRobotPrivateKeyCredentials
          ...

    Returns:
        List[GCPCredential]: credential 列表
    """
    credentials = []
    current_cred = None

    for line in stdout.split('\n'):
        line = line.strip()
        if not line or line.startswith('GCP Service Account'):
            continue

        if line.startswith('ID:'):
            # Save previous credential if exists
            if current_cred:
                credentials.append(current_cred)
            # Start new credential
            cred_id = line.split(':', 1)[1].strip()
            current_cred = GCPCredential(id=cred_id, type="")
        elif line.startswith('Type:') and current_cred:
            current_cred.type = line.split(':', 1)[1].strip()
        elif line.startswith('File Name:') and current_cred:
            current_cred.file_name = line.split(':', 1)[1].strip()
        elif line.startswith('Description:') and current_cred:
            current_cred.description = line.split(':', 1)[1].strip()
        elif line.startswith('Project ID:') and current_cred:
            current_cred.project_id = line.split(':', 1)[1].strip()

    # Don't forget the last credential
    if current_cred:
        credentials.append(current_cred)

    return credentials


def parse_gcp_credential_describe(stdout: str) -> dict:
    """
    解析 gcp credential describe 命令的輸出

    預期格式：
        SUCCESS
        Credential: my-gcp-sa
        Type: GoogleRobotPrivateKeyCredentials
        Scope: GLOBAL
        Project ID: my-gcp-sa
        Service Account: my-sa@project.iam.gserviceaccount.com

        Secret: [PROTECTED]

        Use --show-secret flag to display the full JSON key (use with caution!)

    Returns:
        dict: 包含 credential 資訊的字典
    """
    result = {
        'id': None,
        'type': None,
        'scope': None,
        'file_name': None,
        'description': None,
        'project_id': None,
        'service_account': None,
        'secret_shown': False,
        'has_warning': False
    }

    for line in stdout.split('\n'):
        line = line.strip()
        if line.startswith('Credential:'):
            result['id'] = line.split(':', 1)[1].strip()
        elif line.startswith('Type:'):
            result['type'] = line.split(':', 1)[1].strip()
        elif line.startswith('Scope:'):
            result['scope'] = line.split(':', 1)[1].strip()
        elif line.startswith('File Name:'):
            result['file_name'] = line.split(':', 1)[1].strip()
        elif line.startswith('Description:'):
            result['description'] = line.split(':', 1)[1].strip()
        elif line.startswith('Project ID:'):
            result['project_id'] = line.split(':', 1)[1].strip()
        elif line.startswith('Service Account:'):
            result['service_account'] = line.split(':', 1)[1].strip()
        elif '[PROTECTED]' in line or 'PROTECTED' in line:
            result['secret_shown'] = False
        elif 'WARNING' in line or 'warning' in line.lower():
            result['has_warning'] = True
        elif 'JSON Key Content:' in line or '---' in line:
            result['secret_shown'] = True

    return result


# ============================================================================
# 測試函數 - Help Commands
# ============================================================================
# Note: gcp_sa1_info 和 gcp_sa2_info fixtures 已移至 conftest.py (session scope)

def test_gcp_help(run_jenkee_authed):
    """測試 gcp --help 命令"""
    # Arrange: 使用正確的認證（由 fixture 提供）

    # Act: 執行 gcp --help
    result = run_jenkee_authed.run("gcp", "--help")

    # Assert: 驗證 help 輸出包含預期內容
    assert result.returncode == 0
    assert "gcp <resource> <action>" in result.stdout
    assert "credential" in result.stdout


def test_gcp_credential_help(run_jenkee_authed):
    """測試 gcp credential --help 命令"""
    # Arrange: 使用正確的認證（由 fixture 提供）

    # Act: 執行 gcp credential --help
    result = run_jenkee_authed.run("gcp", "credential", "--help")

    # Assert: 驗證 help 輸出包含所有 actions
    assert result.returncode == 0
    assert "create" in result.stdout
    assert "list" in result.stdout
    assert "describe" in result.stdout
    assert "update" in result.stdout
    assert "delete" in result.stdout


# ============================================================================
# 測試函數 - Create Credential
# ============================================================================

def test_create_gcp_credential(run_jenkee_authed, gcp_key_files, gcp_sa1_info):
    """測試建立 GCP service account credential"""
    # Arrange: 準備 credential ID 和 key file path
    credential_id = "test-new-gcp-cred"

    # Act: 執行 create 指令
    result = run_jenkee_authed.run(
        "gcp", "credential", "create",
        credential_id,
        str(gcp_key_files['sa1'])
    )

    try:
        # Assert: 驗證建立成功
        assert result.returncode == 0, f"Failed to create GCP credential: {result.stderr}"
        assert f"Created GCP credential: {credential_id}" in result.stdout
        assert f"Project ID: {gcp_sa1_info['project_id']}" in result.stdout
        assert f"Service Account: {gcp_sa1_info['client_email']}" in result.stdout
    finally:
        # Cleanup
        run_jenkee_authed.build_command(
            "gcp", "credential", "delete",
            credential_id, "--yes-i-really-mean-it"
        ).allow_failure().run()


def test_create_duplicate_gcp_credential_fails(run_jenkee_authed, gcp_key_files):
    """測試建立重複 ID 的 credential 會失敗"""
    # Arrange: 先建立一個 credential
    credential_id = "test-duplicate-gcp-cred"
    result = run_jenkee_authed.run(
        "gcp", "credential", "create",
        credential_id,
        str(gcp_key_files['sa1'])
    )
    assert result.returncode == 0

    try:
        # Act: 嘗試用相同 ID 建立第二個 credential
        result = run_jenkee_authed.build_command(
            "gcp", "credential", "create",
            credential_id,
            str(gcp_key_files['sa1'])
        ).must_fail().run()

        # Assert: 驗證失敗並顯示適當錯誤訊息
        assert result.returncode != 0
        assert "already exists" in result.stderr.lower()
    finally:
        # Cleanup
        run_jenkee_authed.build_command(
            "gcp", "credential", "delete",
            credential_id, "--yes-i-really-mean-it"
        ).allow_failure().run()


def test_create_gcp_credential_invalid_json(run_jenkee_authed, tmp_path):
    """測試使用無效 JSON file 會被拒絕"""
    # Arrange: 建立無效的 JSON file
    invalid_json = tmp_path / "invalid.json"
    invalid_json.write_text("{ invalid json")

    # Act: 嘗試建立 credential
    result = run_jenkee_authed.build_command(
        "gcp", "credential", "create",
        "test-invalid",
        str(invalid_json)
    ).must_fail().run()

    # Assert: 驗證失敗並顯示 JSON 錯誤
    assert result.returncode != 0
    assert "invalid" in result.stderr.lower() or "json" in result.stderr.lower()


def test_create_gcp_credential_missing_file(run_jenkee_authed):
    """測試使用不存在的 file 會被拒絕"""
    # Arrange: 使用不存在的檔案路徑

    # Act: 嘗試建立 credential
    result = run_jenkee_authed.build_command(
        "gcp", "credential", "create",
        "test-missing",
        "/nonexistent/path/key.json"
    ).must_fail().run()

    # Assert: 驗證失敗並顯示檔案不存在錯誤
    assert result.returncode != 0
    assert "not found" in result.stderr.lower()


def test_create_gcp_credential_incomplete_key(run_jenkee_authed, tmp_path):
    """測試使用不完整的 service account key 會被拒絕"""
    # Arrange: 建立缺少必要欄位的 JSON
    incomplete_key = tmp_path / "incomplete.json"
    incomplete_key.write_text(json.dumps({
        "type": "service_account",
        "project_id": "test-project"
        # 缺少: private_key_id, private_key, client_email
    }))

    # Act: 嘗試建立 credential
    result = run_jenkee_authed.build_command(
        "gcp", "credential", "create",
        "test-incomplete",
        str(incomplete_key)
    ).must_fail().run()

    # Assert: 驗證失敗並顯示缺少欄位錯誤
    assert result.returncode != 0
    assert "missing" in result.stderr.lower() or "fields" in result.stderr.lower()


# ============================================================================
# 測試函數 - List Credentials
# ============================================================================

def test_list_gcp_credentials(run_jenkee_authed, gcp_key_files):
    """測試列出 GCP credentials"""
    # Arrange: 先建立一個測試用的 credential
    credential_id = "test-list-gcp-cred"
    result = run_jenkee_authed.run(
        "gcp", "credential", "create",
        credential_id,
        str(gcp_key_files['sa1'])
    )
    assert result.returncode == 0

    try:
        # Act: 執行 list 指令
        result = run_jenkee_authed.run("gcp", "credential", "list")

        # Parse: 解析輸出
        credentials = parse_gcp_credential_list(result.stdout)

        # Assert: 驗證列出成功並包含建立的 credential
        assert result.returncode == 0
        assert len(credentials) > 0, "Should have at least one credential"

        # 檢查是否包含建立的 credential
        cred_ids = [c.id for c in credentials]
        assert credential_id in cred_ids

        # 驗證類型為 GoogleRobotPrivateKeyCredentials
        for cred in credentials:
            assert "GoogleRobotPrivateKeyCredentials" in cred.type
    finally:
        # Cleanup
        run_jenkee_authed.build_command(
            "gcp", "credential", "delete",
            credential_id, "--yes-i-really-mean-it"
        ).allow_failure().run()


# ============================================================================
# 測試函數 - Describe Credential
# ============================================================================

def test_describe_gcp_credential(run_jenkee_authed, gcp_key_files):
    """測試查看 GCP credential 詳細資訊（不顯示 secret）"""
    # Arrange: 先建立一個測試用的 credential
    credential_id = "test-describe-gcp-cred"
    result = run_jenkee_authed.run(
        "gcp", "credential", "create",
        credential_id,
        str(gcp_key_files['sa1'])
    )
    assert result.returncode == 0

    try:
        # Act: 執行 describe 指令（不帶 --show-secret）
        result = run_jenkee_authed.run("gcp", "credential", "describe", credential_id)

        # Parse: 解析輸出
        info = parse_gcp_credential_describe(result.stdout)

        # Assert: 驗證輸出正確且不顯示 secret
        assert result.returncode == 0
        assert info['id'] == credential_id
        assert info['secret_shown'] is False
        assert "show-secret" in result.stdout.lower()
    finally:
        # Cleanup
        run_jenkee_authed.build_command(
            "gcp", "credential", "delete",
            credential_id, "--yes-i-really-mean-it"
        ).allow_failure().run()


def test_describe_gcp_credential_with_secret(run_jenkee_authed, gcp_key_files, gcp_sa1_info):
    """測試查看 GCP credential 並顯示 secret"""
    # Arrange: 先建立一個測試用的 credential
    credential_id = "test-describe-secret-cred"
    result = run_jenkee_authed.run(
        "gcp", "credential", "create",
        credential_id,
        str(gcp_key_files['sa1'])
    )
    assert result.returncode == 0

    try:
        # Act: 執行 describe 指令（帶 --show-secret）
        result = run_jenkee_authed.run(
            "gcp", "credential", "describe",
            credential_id,
            "--show-secret"
        )

        # Parse: 解析輸出
        info = parse_gcp_credential_describe(result.stdout)

        # Assert: 驗證顯示 secret 並包含警告
        assert result.returncode == 0
        assert gcp_sa1_info['project_id'] in result.stdout
        assert gcp_sa1_info['client_email'] in result.stdout
        assert info['has_warning'] is True
    finally:
        # Cleanup
        run_jenkee_authed.build_command(
            "gcp", "credential", "delete",
            credential_id, "--yes-i-really-mean-it"
        ).allow_failure().run()


def test_describe_nonexistent_credential_fails(run_jenkee_authed):
    """測試查看不存在的 credential 會失敗"""
    # Arrange: 使用不存在的 credential ID

    # Act: 嘗試 describe 不存在的 credential
    result = run_jenkee_authed.build_command(
        "gcp", "credential", "describe",
        "nonexistent-credential-id"
    ).must_fail().run()

    # Assert: 驗證失敗並顯示適當錯誤訊息
    assert result.returncode != 0
    assert "not found" in result.stderr.lower()


# ============================================================================
# 測試函數 - Update Credential
# ============================================================================

def test_update_gcp_credential(run_jenkee_authed, gcp_key_files, gcp_sa1_info, gcp_sa2_info):
    """測試更新現有的 GCP credential（key rotation 情境）"""
    # Arrange: 先用 SA-1 建立一個 credential
    credential_id = "test-update-gcp-cred"
    result = run_jenkee_authed.run(
        "gcp", "credential", "create",
        credential_id,
        str(gcp_key_files['sa1'])
    )
    assert result.returncode == 0

    try:
        # Act: 更新 credential 使用 SA-2 的 key（模擬 key rotation）
        result = run_jenkee_authed.run(
            "gcp", "credential", "update",
            credential_id,
            str(gcp_key_files['sa2'])
        )

        # Assert: 驗證更新成功，並且 project ID 變成 SA-2 的
        assert result.returncode == 0, f"Failed to update GCP credential: {result.stderr}"
        assert f"Updated GCP credential: {credential_id}" in result.stdout
        assert f"Project ID: {gcp_sa2_info['project_id']}" in result.stdout
        assert f"Service Account: {gcp_sa2_info['client_email']}" in result.stdout
    finally:
        # Cleanup
        run_jenkee_authed.build_command(
            "gcp", "credential", "delete",
            credential_id, "--yes-i-really-mean-it"
        ).allow_failure().run()


def test_update_nonexistent_credential_fails(run_jenkee_authed, gcp_key_files):
    """測試更新不存在的 credential 會失敗"""
    # Arrange: 使用不存在的 credential ID

    # Act: 嘗試更新不存在的 credential
    result = run_jenkee_authed.build_command(
        "gcp", "credential", "update",
        "nonexistent-credential-id",
        str(gcp_key_files['sa1'])
    ).must_fail().run()

    # Assert: 驗證失敗並顯示適當錯誤訊息
    assert result.returncode != 0
    assert "not found" in result.stderr.lower()


# ============================================================================
# 測試函數 - Delete Credential
# ============================================================================

def test_delete_gcp_credential(run_jenkee_authed, gcp_key_files):
    """測試刪除 GCP credential（使用 --yes-i-really-mean-it flag）"""
    # Arrange: 先建立一個 credential
    credential_id = "test-delete-gcp-cred"
    result = run_jenkee_authed.run(
        "gcp", "credential", "create",
        credential_id,
        str(gcp_key_files['sa1'])
    )
    assert result.returncode == 0

    # Act: 刪除 credential（使用 --yes-i-really-mean-it 跳過互動式確認）
    result = run_jenkee_authed.run(
        "gcp", "credential", "delete",
        credential_id,
        "--yes-i-really-mean-it"
    )

    # Assert: 驗證刪除成功
    assert result.returncode == 0, f"Failed to delete GCP credential: {result.stderr}"
    assert f"Deleted GCP credential: {credential_id}" in result.stdout

    # Verify: 驗證 credential 確實被刪除
    result = run_jenkee_authed.build_command(
        "gcp", "credential", "describe", credential_id
    ).must_fail().run()
    assert result.returncode != 0
    assert "not found" in result.stderr.lower()


def test_delete_gcp_credential_with_confirmation_cancelled(run_jenkee_authed, gcp_key_files):
    """
    測試取消刪除 GCP credential（模擬輸入 n）

    對應文件中的「測試 2: 取消刪除」
    """
    # Arrange: 先建立一個 credential
    credential_id = "test-delete-gcp-cred-cancel"
    result = run_jenkee_authed.run(
        "gcp", "credential", "create",
        credential_id,
        str(gcp_key_files['sa1'])
    )
    assert result.returncode == 0

    try:
        # Act: 嘗試刪除但取消（模擬輸入 'n'）
        result = run_jenkee_authed.build_command(
            "gcp", "credential", "delete",
            credential_id
        ).with_stdin("n\n").run()

        # Assert: 驗證返回 0（取消不是錯誤）
        assert result.returncode == 0, f"Should return 0 when cancelled, got: {result.returncode}"
        assert "cancelled" in result.stdout.lower() or "canceled" in result.stdout.lower(), \
            "Should show cancellation message"

        # Verify: credential 仍然存在
        describe_result = run_jenkee_authed.run(
            "gcp", "credential", "describe", credential_id
        )
        assert describe_result.returncode == 0, "Credential should still exist after cancellation"
    finally:
        # Cleanup
        run_jenkee_authed.build_command(
            "gcp", "credential", "delete",
            credential_id, "--yes-i-really-mean-it"
        ).allow_failure().run()


def test_delete_gcp_credential_with_confirmation_confirmed(run_jenkee_authed, gcp_key_files):
    """
    測試互動式確認後刪除 GCP credential（模擬輸入 y）

    對應文件中的「測試 1: 互動式確認」
    """
    # Arrange: 先建立一個 credential
    credential_id = "test-delete-gcp-cred-confirm"
    result = run_jenkee_authed.run(
        "gcp", "credential", "create",
        credential_id,
        str(gcp_key_files['sa1'])
    )
    assert result.returncode == 0

    # Act: 刪除並確認（模擬輸入 'y'）
    result = run_jenkee_authed.build_command(
        "gcp", "credential", "delete",
        credential_id
    ).with_stdin("y\n").run()

    # Assert: 驗證刪除成功
    assert result.returncode == 0, f"Failed to delete GCP credential: {result.stderr}"
    assert f"Deleted GCP credential: {credential_id}" in result.stdout

    # Verify: 驗證 credential 確實被刪除
    result = run_jenkee_authed.build_command(
        "gcp", "credential", "describe", credential_id
    ).must_fail().run()
    assert result.returncode != 0
    assert "not found" in result.stderr.lower()


def test_delete_nonexistent_credential_fails(run_jenkee_authed):
    """測試刪除不存在的 credential 會失敗"""
    # Arrange: 使用不存在的 credential ID

    # Act: 嘗試刪除不存在的 credential
    result = run_jenkee_authed.build_command(
        "gcp", "credential", "delete",
        "nonexistent-credential-id",
        "--yes-i-really-mean-it"
    ).must_fail().run()

    # Assert: 驗證失敗並顯示適當錯誤訊息
    assert result.returncode != 0
    assert "not found" in result.stderr.lower()
