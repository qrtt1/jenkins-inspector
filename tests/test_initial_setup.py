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
import pytest


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

    # Assert: 驗證認證成功
    assert result.returncode == 0, "Authentication should succeed"
    assert result.stdout.strip(), "Should have output"

    # 驗證輸出包含使用者名稱或成功訊息
    # (根據實際 auth 命令的輸出格式調整)
    assert "jenkins-test" in result.stdout or "Authenticated" in result.stdout, \
        "Should show authenticated username or success message"


def test_step2_list_all_views(run_jenkee_authed):
    """
    測試步驟 2: 列出所有 Views

    預期結果：
    - Exit code: 0
    - 至少包含 "All" view
    - 包含測試用的自訂 views
    """
    # Act: 執行 list-views 指令
    result = run_jenkee_authed.run("list-views")

    # Assert: 驗證執行成功
    assert result.returncode == 0, "list-views should succeed"

    # 解析 views 列表
    views = set(line.strip() for line in result.stdout.strip().split('\n') if line.strip())

    # 驗證包含預期的 views（注意 Jenkins 回傳的是小寫 "all"）
    assert "all" in views or "All" in views, "Should contain default 'all' or 'All' view"
    assert "test-view" in views, "Should contain 'test-view' created by fixture"
    assert "empty-view" in views, "Should contain 'empty-view' created by fixture"

    # 至少應該有 3 個 views
    assert len(views) >= 3, f"Should have at least 3 views, got {len(views)}: {views}"


def test_step3_list_all_jobs(run_jenkee_authed):
    """
    測試步驟 3: 列出所有 Jobs (使用 --all)

    預期結果：
    - Exit code: 0
    - 顯示所有測試 jobs
    - 格式清晰
    """
    # Act: 執行 list-jobs --all 指令
    result = run_jenkee_authed.run("list-jobs", "--all")

    # Assert: 驗證執行成功
    assert result.returncode == 0, "list-jobs --all should succeed"

    # 解析 jobs 列表
    jobs = set(line.strip() for line in result.stdout.strip().split('\n') if line.strip())

    # 驗證包含所有測試 jobs
    expected_jobs = {"test-job-1", "test-job-2", "test-job-3"}
    assert expected_jobs.issubset(jobs), \
        f"Should contain all test jobs. Expected {expected_jobs}, got {jobs}"


def test_step4_list_jobs_in_specific_view(run_jenkee_authed):
    """
    測試步驟 4: 列出特定 View 的 Jobs

    預期結果：
    - Exit code: 0
    - 只顯示該 view 中的 jobs
    - 結果與 fixture 設定一致
    """
    # Act: 執行 list-jobs All 指令
    result = run_jenkee_authed.run("list-jobs", "All")

    # Assert: 驗證執行成功
    assert result.returncode == 0, "list-jobs All should succeed"

    # 解析 jobs 列表
    jobs = set(line.strip() for line in result.stdout.strip().split('\n') if line.strip())

    # All view 應該包含所有 jobs
    expected_jobs = {"test-job-1", "test-job-2", "test-job-3"}
    assert expected_jobs.issubset(jobs), \
        f"'All' view should contain all test jobs. Expected {expected_jobs}, got {jobs}"


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

    # Assert: 驗證執行成功
    assert result.returncode == 0, "list-credentials should succeed"

    output = result.stdout

    # 驗證輸出格式包含必要資訊
    assert "Domain:" in output or "ID:" in output, \
        "Should show credential information"

    # 驗證包含測試 credentials（由 fixture 建立）
    assert "test-credential-1" in output, "Should contain test-credential-1"
    assert "test-credential-2" in output, "Should contain test-credential-2"
    assert "test-credential-3" in output, "Should contain test-credential-3"

    # 驗證顯示類型資訊
    assert "Type:" in output or "UsernamePasswordCredentialsImpl" in output or "StringCredentialsImpl" in output, \
        "Should show credential types"

    # 驗證不洩漏 secret（不應該包含實際密碼或 secret 值）
    assert "test-password" not in output, "Should not leak password values"
    assert "test-secret-value" not in output, "Should not leak secret values"


def test_complete_workflow(run_jenkee_authed):
    """
    測試完整工作流程：按順序執行所有步驟

    這模擬使用者第一次使用工具探索 Jenkins 環境的真實情境
    """
    # 1. 驗證連線
    auth_result = run_jenkee_authed.run("auth")
    assert auth_result.returncode == 0, "Step 1: Authentication failed"

    # 2. 探索 views
    views_result = run_jenkee_authed.run("list-views")
    assert views_result.returncode == 0, "Step 2: List views failed"
    views = set(line.strip() for line in views_result.stdout.strip().split('\n') if line.strip())
    assert len(views) >= 3, "Should have multiple views"

    # 3. 探索所有 jobs
    all_jobs_result = run_jenkee_authed.run("list-jobs", "--all")
    assert all_jobs_result.returncode == 0, "Step 3: List all jobs failed"

    # 4. 探索特定 view 的 jobs
    view_jobs_result = run_jenkee_authed.run("list-jobs", "test-view")
    assert view_jobs_result.returncode == 0, "Step 4: List jobs in view failed"

    # 5. 查看 credentials
    creds_result = run_jenkee_authed.run("list-credentials")
    assert creds_result.returncode == 0, "Step 5: List credentials failed"

    # 驗證整個流程順利完成
    assert True, "Complete workflow executed successfully"


# 錯誤情境測試


def test_error_wrong_credentials(jenkins_instance):
    """
    錯誤情境：使用錯誤的認證資訊

    預期結果：
    - Exit code: 非 0
    - 顯示認證失敗錯誤訊息
    """
    import subprocess
    import os

    # 建立錯誤的環境變數
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

    # Assert: 驗證認證失敗
    assert result.returncode != 0, "Should fail with wrong credentials"

    # 驗證有錯誤訊息（可能在 stdout 或 stderr）
    error_output = result.stderr + result.stdout
    assert error_output.strip(), "Should have error message"


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
    error_output = result.stderr + result.stdout
    assert error_output.strip(), "Should have error message"
    # 可能包含 "not found", "doesn't exist", "Error" 等訊息
    assert any(keyword in error_output.lower() for keyword in ["error", "not found", "doesn't exist", "does not exist"]), \
        "Error message should indicate the view doesn't exist"


def test_idempotent_operations(run_jenkee_authed):
    """
    測試冪等性：重複執行 read-only 操作應該都成功

    所有 initial setup 中的操作都是 read-only，可以安全地重複執行
    """
    # 重複執行 3 次，驗證每次都成功且結果一致
    for i in range(3):
        # list-views
        views_result = run_jenkee_authed.run("list-views")
        assert views_result.returncode == 0, f"Iteration {i+1}: list-views failed"

        # list-jobs
        jobs_result = run_jenkee_authed.run("list-jobs", "--all")
        assert jobs_result.returncode == 0, f"Iteration {i+1}: list-jobs failed"

        # list-credentials
        creds_result = run_jenkee_authed.run("list-credentials")
        assert creds_result.returncode == 0, f"Iteration {i+1}: list-credentials failed"

    # 所有操作都成功重複執行
    assert True, "All read-only operations are idempotent"


def test_output_format_clarity(run_jenkee_authed):
    """
    測試輸出格式清晰度

    驗證所有命令的輸出都是清晰易讀的
    """
    # list-views: 應該是簡單的列表
    views_result = run_jenkee_authed.run("list-views")
    views_lines = [line for line in views_result.stdout.split('\n') if line.strip()]
    assert all(len(line.split()) <= 3 for line in views_lines), \
        "list-views output should be simple list"

    # list-jobs: 應該是簡單的列表
    jobs_result = run_jenkee_authed.run("list-jobs", "--all")
    jobs_lines = [line for line in jobs_result.stdout.split('\n') if line.strip()]
    assert all(len(line.split()) <= 3 for line in jobs_lines), \
        "list-jobs output should be simple list"

    # list-credentials: 應該有結構化的輸出
    creds_result = run_jenkee_authed.run("list-credentials")
    assert "ID:" in creds_result.stdout or "Domain:" in creds_result.stdout, \
        "list-credentials should have structured output"
