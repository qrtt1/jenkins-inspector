"""
測試 Job Organization and Status Management 相關指令

涵蓋指令：
- job-status: 查看 job 狀態與觸發關係
- add-job-to-view: 將 jobs 加入 view
- enable-job: 啟用 job
- disable-job: 停用 job

測試重點：
- 驗證 job 狀態查詢功能
- 測試將 jobs 組織到 views
- 測試啟用/停用 job 的完整流程
- 驗證冪等性與批次操作
"""
import re
from dataclasses import dataclass
from typing import List, Optional, Set


# ============================================================================
# Parser Functions - 將命令輸出解析為可精確比對的資料結構
# ============================================================================


@dataclass
class JobStatusInfo:
    """Job 狀態的結構化資料"""
    name: str
    status: str  # "ENABLED" or "DISABLED"
    buildable: bool
    last_build: Optional[int] = None
    last_stable_build: Optional[int] = None
    last_successful_build: Optional[int] = None
    last_failed_build: Optional[int] = None
    downstream_projects: List[str] = None
    upstream_projects: List[str] = None

    def __post_init__(self):
        if self.downstream_projects is None:
            self.downstream_projects = []
        if self.upstream_projects is None:
            self.upstream_projects = []


def parse_job_status(stdout: str) -> JobStatusInfo:
    """
    解析 job-status 命令的輸出

    預期格式：
        === Job: test-job-1 ===

        Status: ENABLED
        Buildable: true

        === Health ===
        ...

        === Last Builds ===
        Last Build: #5
        Last Stable Build: #4
        ...

        === Downstream Projects ===
          - downstream-job-1
          (none)

        === Upstream Projects ===
          - upstream-job-1
          (none)

    Returns:
        JobStatusInfo: 結構化的 job 狀態資料
    """
    lines = stdout.split('\n')

    name = None
    status = None
    buildable = False
    last_build = None
    last_stable_build = None
    last_successful_build = None
    last_failed_build = None
    downstream_projects = []
    upstream_projects = []

    current_section = None

    for line in lines:
        line_stripped = line.strip()

        # Job header
        if line_stripped.startswith('=== Job:'):
            match = re.search(r'===\s*Job:\s*(.+?)\s*===', line_stripped)
            if match:
                name = match.group(1)

        # Status
        elif line_stripped.startswith('Status:'):
            status = line_stripped.split(':', 1)[1].strip()

        # Buildable
        elif line_stripped.startswith('Buildable:'):
            buildable_str = line_stripped.split(':', 1)[1].strip().lower()
            buildable = buildable_str == 'true'

        # Section headers
        elif '=== Last Builds ===' in line_stripped:
            current_section = 'builds'
        elif '=== Downstream Projects ===' in line_stripped:
            current_section = 'downstream'
        elif '=== Upstream Projects ===' in line_stripped:
            current_section = 'upstream'

        # Last builds
        elif current_section == 'builds':
            if line_stripped.startswith('Last Build:'):
                match = re.search(r'#(\d+)', line_stripped)
                if match:
                    last_build = int(match.group(1))
            elif line_stripped.startswith('Last Stable Build:'):
                match = re.search(r'#(\d+)', line_stripped)
                if match:
                    last_stable_build = int(match.group(1))
            elif line_stripped.startswith('Last Successful Build:'):
                match = re.search(r'#(\d+)', line_stripped)
                if match:
                    last_successful_build = int(match.group(1))
            elif line_stripped.startswith('Last Failed Build:'):
                match = re.search(r'#(\d+)', line_stripped)
                if match:
                    last_failed_build = int(match.group(1))

        # Downstream projects
        elif current_section == 'downstream':
            if line_stripped.startswith('- '):
                project = line_stripped[2:].strip()
                if project and project != '(none)':
                    downstream_projects.append(project)

        # Upstream projects
        elif current_section == 'upstream':
            if line_stripped.startswith('- '):
                project = line_stripped[2:].strip()
                if project and project != '(none)':
                    upstream_projects.append(project)

    return JobStatusInfo(
        name=name or '',
        status=status or 'UNKNOWN',
        buildable=buildable,
        last_build=last_build,
        last_stable_build=last_stable_build,
        last_successful_build=last_successful_build,
        last_failed_build=last_failed_build,
        downstream_projects=downstream_projects,
        upstream_projects=upstream_projects
    )


def parse_jobs_list(stdout: str) -> Set[str]:
    """
    解析 list-jobs 命令的輸出

    預期格式：每行一個 job 名稱
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
        if line and not line.startswith('==='):  # 跳過空行與分隔線
            jobs.add(line)

    return jobs


# ============================================================================
# 測試函數 - Job-Status 指令
# ============================================================================


def test_job_status_basic(run_jenkee_authed):
    """
    測試查看 Job 狀態

    對應 test plan 步驟 1
    """
    # Arrange: 使用已認證的 jenkee runner（由 fixture 提供）

    # Act: 執行 job-status 指令
    result = run_jenkee_authed.run("job-status", "test-job-1")

    # Parse: 解析 job 狀態
    status = parse_job_status(result.stdout)

    # Assert: 驗證執行成功
    assert result.returncode == 0, f"job-status should succeed, got: {result.stderr}"
    assert status.name == "test-job-1", f"Expected job name test-job-1, got {status.name}"
    assert status.status in ["ENABLED", "DISABLED"], \
        f"Status should be ENABLED or DISABLED, got {status.status}"


def test_job_status_shows_build_info(run_jenkee_authed):
    """
    測試 job-status 顯示 Build 資訊

    驗證輸出包含 last build 相關資訊
    """
    # Arrange: 先觸發一個 build 確保有 build history
    build_result = run_jenkee_authed.run("build", "test-job-1")
    assert build_result.returncode == 0, "Should trigger build successfully"

    # Act: 執行 job-status 指令
    result = run_jenkee_authed.run("job-status", "test-job-1")

    # Parse: 解析 job 狀態
    status = parse_job_status(result.stdout)

    # Assert: 驗證包含 build 資訊
    assert result.returncode == 0
    assert status.last_build is not None, "Should have last build information"


def test_job_status_nonexistent(run_jenkee_authed):
    """
    測試查看不存在的 Job 狀態

    對應 test plan 錯誤情境測試
    """
    # Arrange: 使用不存在的 job 名稱

    # Act: 執行 job-status 指令並允許失敗
    result = run_jenkee_authed.build_command(
        "job-status", "non-existent-job"
    ).allow_failure().run()

    # Assert: 驗證失敗
    assert result.returncode != 0, "Should fail for non-existent job"
    error_output = (result.stdout + result.stderr).lower()
    assert 'error' in error_output or 'not found' in error_output, \
        f"Should have error message, got: {result.stdout + result.stderr}"


# ============================================================================
# 測試函數 - Add-Job-To-View 指令
# ============================================================================


def test_add_job_to_view_single(run_jenkee_authed):
    """
    測試將單一 Job 加入 View

    對應 test plan 步驟 2
    """
    # Arrange: 使用已存在的 test-view 和 test-job-3
    # test-view 已經包含 test-job-1 和 test-job-2，我們加入 test-job-3

    # Act: 執行 add-job-to-view 指令
    result = run_jenkee_authed.run("add-job-to-view", "test-view", "test-job-3")

    # Assert: 驗證執行成功
    assert result.returncode == 0, f"add-job-to-view should succeed, got: {result.stderr}"
    assert "✓" in result.stdout or "success" in result.stdout.lower(), \
        "Should show success message"


def test_verify_job_in_view(run_jenkee_authed):
    """
    測試驗證 Job 已加入 View

    對應 test plan 步驟 3
    """
    # Arrange: 先將 job 加入 view
    add_result = run_jenkee_authed.run("add-job-to-view", "test-view", "test-job-3")
    assert add_result.returncode == 0, "Should add job successfully"

    # Act: 執行 list-jobs 指令查看 view 中的 jobs
    result = run_jenkee_authed.run("list-jobs", "test-view")

    # Parse: 解析 jobs 列表
    jobs = parse_jobs_list(result.stdout)

    # Assert: 驗證 job 存在於 view 中
    assert result.returncode == 0
    assert "test-job-3" in jobs, \
        f"test-job-3 should be in test-view, got: {jobs}"


def test_add_job_to_view_multiple(run_jenkee_authed):
    """
    測試批次將多個 Jobs 加入 View

    對應 test plan 步驟 4
    """
    # Arrange: 使用已存在的 test-view
    # test-view 已經包含 test-job-1 和 test-job-2
    # 我們加入 test-job-3 和 long-running-job

    # Act: 執行 add-job-to-view 指令（批次）
    result = run_jenkee_authed.run(
        "add-job-to-view", "test-view", "test-job-3", "long-running-job"
    )

    # Assert: 驗證執行成功
    assert result.returncode == 0, f"add-job-to-view should succeed, got: {result.stderr}"
    assert "✓" in result.stdout or "success" in result.stdout.lower(), \
        "Should show success message"

    # Verify: 驗證所有 jobs 都加入了
    list_result = run_jenkee_authed.run("list-jobs", "test-view")
    jobs = parse_jobs_list(list_result.stdout)

    assert "test-job-3" in jobs, "test-job-3 should be in view"
    assert "long-running-job" in jobs, "long-running-job should be in view"


def test_add_job_to_view_idempotent(run_jenkee_authed):
    """
    測試冪等性（重複加入相同 Job）

    對應 test plan 步驟 5
    """
    # Arrange: 先加入一次（test-job-1 在 test-view 可能已經存在）
    first_result = run_jenkee_authed.run("add-job-to-view", "test-view", "test-job-1")
    assert first_result.returncode == 0, "First add should succeed"

    # Act: 再次加入相同的 job（測試冪等性）
    second_result = run_jenkee_authed.run("add-job-to-view", "test-view", "test-job-1")

    # Assert: 驗證操作成功（冪等）
    assert second_result.returncode == 0, \
        "Second add should also succeed (idempotent operation)"

    # Verify: 驗證 job 只出現一次
    list_result = run_jenkee_authed.run("list-jobs", "test-view")
    jobs_list = list_result.stdout.strip().split('\n')
    test_job_1_count = sum(1 for job in jobs_list if job.strip() == "test-job-1")

    assert test_job_1_count == 1, \
        f"test-job-1 should appear exactly once, but appeared {test_job_1_count} times"


def test_add_job_to_nonexistent_view(run_jenkee_authed):
    """
    測試將 Job 加入不存在的 View

    對應 test plan 錯誤情境測試
    """
    # Arrange: 使用不存在的 view 名稱

    # Act: 執行 add-job-to-view 指令並允許失敗
    result = run_jenkee_authed.build_command(
        "add-job-to-view", "non-existent-view", "test-job-1"
    ).allow_failure().run()

    # Assert: 驗證失敗
    assert result.returncode != 0, "Should fail for non-existent view"
    error_output = (result.stdout + result.stderr).lower()
    assert 'error' in error_output or 'not found' in error_output or 'no such' in error_output, \
        f"Should have error message, got: {result.stdout + result.stderr}"


# ============================================================================
# 測試函數 - Enable/Disable Job 指令
# ============================================================================


def test_disable_job(run_jenkee_authed):
    """
    測試停用 Job

    對應 test plan 步驟 6
    注意：測試後會恢復 job 狀態
    """
    # Arrange: 確保 test-job-3 初始是啟用的
    enable_result = run_jenkee_authed.run(
        "enable-job", "test-job-3", "--yes-i-really-mean-it"
    )
    assert enable_result.returncode == 0, "Should enable job first"

    # Act: 執行 disable-job 指令
    result = run_jenkee_authed.run(
        "disable-job", "test-job-3", "--yes-i-really-mean-it"
    )

    # Assert: 驗證執行成功
    assert result.returncode == 0, f"disable-job should succeed, got: {result.stderr}"
    assert "✓" in result.stdout or "success" in result.stdout.lower(), \
        "Should show success message"

    # Cleanup: 恢復 job 狀態（啟用）
    cleanup_result = run_jenkee_authed.run(
        "enable-job", "test-job-3", "--yes-i-really-mean-it"
    )
    assert cleanup_result.returncode == 0, "Should restore job state"


def test_disable_job_with_confirmation_cancelled(run_jenkee_authed):
    """
    測試取消停用 Job（模擬輸入 n）

    對應文件中的「測試 2: 取消停用」
    """
    # Arrange: 確保 test-job-3 初始是啟用的
    enable_result = run_jenkee_authed.run(
        "enable-job", "test-job-3", "--yes-i-really-mean-it"
    )
    assert enable_result.returncode == 0, "Should enable job first"

    # Act: 嘗試停用但取消（模擬輸入 'n'）
    result = run_jenkee_authed.build_command(
        "disable-job", "test-job-3"
    ).with_stdin("n\n").run()

    # Assert: 驗證返回 0（取消不是錯誤）
    assert result.returncode == 0, f"Should return 0 when cancelled, got: {result.returncode}"
    assert "cancelled" in result.stdout.lower() or "canceled" in result.stdout.lower(), \
        "Should show cancellation message"

    # Verify: job 仍然是啟用狀態
    status_result = run_jenkee_authed.run("job-status", "test-job-3")
    status = parse_job_status(status_result.stdout)
    assert status.status == "ENABLED", "Job should remain enabled after cancellation"


def test_disable_job_with_confirmation_confirmed(run_jenkee_authed):
    """
    測試互動式確認後停用 Job（模擬輸入 y）

    對應文件中的「測試 1: 互動式確認」
    """
    # Arrange: 確保 test-job-3 初始是啟用的
    enable_result = run_jenkee_authed.run(
        "enable-job", "test-job-3", "--yes-i-really-mean-it"
    )
    assert enable_result.returncode == 0, "Should enable job first"

    # Act: 停用並確認（模擬輸入 'y'）
    result = run_jenkee_authed.build_command(
        "disable-job", "test-job-3"
    ).with_stdin("y\n").run()

    # Assert: 驗證執行成功
    assert result.returncode == 0, f"disable-job should succeed, got: {result.stderr}"
    assert "✓" in result.stdout or "success" in result.stdout.lower(), \
        "Should show success message"

    # Verify: job 已停用
    status_result = run_jenkee_authed.run("job-status", "test-job-3")
    status = parse_job_status(status_result.stdout)
    assert status.status == "DISABLED", "Job should be disabled after confirmation"

    # Cleanup: 恢復 job 狀態（啟用）
    cleanup_result = run_jenkee_authed.run(
        "enable-job", "test-job-3", "--yes-i-really-mean-it"
    )
    assert cleanup_result.returncode == 0, "Should restore job state"


def test_verify_job_disabled(run_jenkee_authed):
    """
    測試驗證 Job 已停用

    對應 test plan 步驟 7
    """
    # Arrange: 先停用 job
    disable_result = run_jenkee_authed.run(
        "disable-job", "test-job-3", "--yes-i-really-mean-it"
    )
    assert disable_result.returncode == 0, "Should disable job successfully"

    # Act: 執行 job-status 指令查看狀態
    result = run_jenkee_authed.run("job-status", "test-job-3")

    # Parse: 解析 job 狀態
    status = parse_job_status(result.stdout)

    # Assert: 驗證狀態為 DISABLED
    assert result.returncode == 0
    assert status.status == "DISABLED", \
        f"Job should be DISABLED, got {status.status}"

    # Cleanup: 恢復 job 狀態
    cleanup_result = run_jenkee_authed.run(
        "enable-job", "test-job-3", "--yes-i-really-mean-it"
    )
    assert cleanup_result.returncode == 0, "Should restore job state"


def test_build_disabled_job(run_jenkee_authed):
    """
    測試嘗試觸發已停用的 Job

    對應 test plan 步驟 8
    """
    # Arrange: 先停用 job
    disable_result = run_jenkee_authed.run(
        "disable-job", "test-job-3", "--yes-i-really-mean-it"
    )
    assert disable_result.returncode == 0, "Should disable job successfully"

    # Act: 嘗試觸發 build 並允許失敗
    result = run_jenkee_authed.build_command("build", "test-job-3").allow_failure().run()

    # Assert: 驗證失敗或顯示警告
    # 注意：Jenkins 的行為可能是失敗或成功但不執行
    # 我們只驗證有適當的訊息
    output = (result.stdout + result.stderr).lower()
    # 可能的情況：失敗、或成功但提示 job 已停用
    assert result.returncode != 0 or 'disabled' in output or 'not buildable' in output, \
        "Should fail or warn about disabled job"

    # Cleanup: 恢復 job 狀態
    cleanup_result = run_jenkee_authed.run(
        "enable-job", "test-job-3", "--yes-i-really-mean-it"
    )
    assert cleanup_result.returncode == 0, "Should restore job state"


def test_enable_job(run_jenkee_authed):
    """
    測試重新啟用 Job

    對應 test plan 步驟 9
    """
    # Arrange: 先停用 job
    disable_result = run_jenkee_authed.run(
        "disable-job", "test-job-3", "--yes-i-really-mean-it"
    )
    assert disable_result.returncode == 0, "Should disable job first"

    # Act: 執行 enable-job 指令
    result = run_jenkee_authed.run(
        "enable-job", "test-job-3", "--yes-i-really-mean-it"
    )

    # Assert: 驗證執行成功
    assert result.returncode == 0, f"enable-job should succeed, got: {result.stderr}"
    assert "✓" in result.stdout or "success" in result.stdout.lower(), \
        "Should show success message"


def test_enable_job_with_confirmation_cancelled(run_jenkee_authed):
    """
    測試取消啟用 Job（模擬輸入 n）

    對應文件中的「測試 2: 取消啟用」
    """
    # Arrange: 確保 test-job-3 初始是停用的
    disable_result = run_jenkee_authed.run(
        "disable-job", "test-job-3", "--yes-i-really-mean-it"
    )
    assert disable_result.returncode == 0, "Should disable job first"

    # Act: 嘗試啟用但取消（模擬輸入 'n'）
    result = run_jenkee_authed.build_command(
        "enable-job", "test-job-3"
    ).with_stdin("n\n").run()

    # Assert: 驗證返回 0（取消不是錯誤）
    assert result.returncode == 0, f"Should return 0 when cancelled, got: {result.returncode}"
    assert "cancelled" in result.stdout.lower() or "canceled" in result.stdout.lower(), \
        "Should show cancellation message"

    # Verify: job 仍然是停用狀態
    status_result = run_jenkee_authed.run("job-status", "test-job-3")
    status = parse_job_status(status_result.stdout)
    assert status.status == "DISABLED", "Job should remain disabled after cancellation"


def test_enable_job_with_confirmation_confirmed(run_jenkee_authed):
    """
    測試互動式確認後啟用 Job（模擬輸入 y）

    對應文件中的「測試 1: 互動式確認」
    """
    # Arrange: 確保 test-job-3 初始是停用的
    disable_result = run_jenkee_authed.run(
        "disable-job", "test-job-3", "--yes-i-really-mean-it"
    )
    assert disable_result.returncode == 0, "Should disable job first"

    # Act: 啟用並確認（模擬輸入 'y'）
    result = run_jenkee_authed.build_command(
        "enable-job", "test-job-3"
    ).with_stdin("y\n").run()

    # Assert: 驗證執行成功
    assert result.returncode == 0, f"enable-job should succeed, got: {result.stderr}"
    assert "✓" in result.stdout or "success" in result.stdout.lower(), \
        "Should show success message"

    # Verify: job 已啟用
    status_result = run_jenkee_authed.run("job-status", "test-job-3")
    status = parse_job_status(status_result.stdout)
    assert status.status == "ENABLED", "Job should be enabled after confirmation"


def test_verify_job_enabled(run_jenkee_authed):
    """
    測試驗證 Job 已啟用

    對應 test plan 步驟 10
    """
    # Arrange: 先停用再啟用 job
    disable_result = run_jenkee_authed.run(
        "disable-job", "test-job-3", "--yes-i-really-mean-it"
    )
    assert disable_result.returncode == 0, "Should disable job first"

    enable_result = run_jenkee_authed.run(
        "enable-job", "test-job-3", "--yes-i-really-mean-it"
    )
    assert enable_result.returncode == 0, "Should enable job successfully"

    # Act: 執行 job-status 指令查看狀態
    result = run_jenkee_authed.run("job-status", "test-job-3")

    # Parse: 解析 job 狀態
    status = parse_job_status(result.stdout)

    # Assert: 驗證狀態為 ENABLED
    assert result.returncode == 0
    assert status.status == "ENABLED", \
        f"Job should be ENABLED, got {status.status}"

    # Verify: 驗證可以觸發 build
    build_result = run_jenkee_authed.run("build", "test-job-3")
    assert build_result.returncode == 0, "Should be able to trigger build"


def test_disable_multiple_jobs(run_jenkee_authed):
    """
    測試批次停用多個 Jobs

    對應 test plan 步驟 11
    """
    # Arrange: 確保 jobs 初始是啟用的
    enable_result = run_jenkee_authed.run(
        "enable-job", "test-job-1", "test-job-2", "--yes-i-really-mean-it"
    )
    assert enable_result.returncode == 0, "Should enable jobs first"

    # Act: 執行 disable-job 指令（批次）
    result = run_jenkee_authed.run(
        "disable-job", "test-job-1", "test-job-2", "--yes-i-really-mean-it"
    )

    # Assert: 驗證執行成功
    assert result.returncode == 0, f"disable-job should succeed, got: {result.stderr}"
    assert "✓" in result.stdout or "success" in result.stdout.lower(), \
        "Should show success message"

    # Verify: 驗證所有 jobs 都被停用
    status1_result = run_jenkee_authed.run("job-status", "test-job-1")
    status1 = parse_job_status(status1_result.stdout)
    assert status1.status == "DISABLED", "test-job-1 should be disabled"

    status2_result = run_jenkee_authed.run("job-status", "test-job-2")
    status2 = parse_job_status(status2_result.stdout)
    assert status2.status == "DISABLED", "test-job-2 should be disabled"

    # Cleanup: 恢復 jobs 狀態
    cleanup_result = run_jenkee_authed.run(
        "enable-job", "test-job-1", "test-job-2", "--yes-i-really-mean-it"
    )
    assert cleanup_result.returncode == 0, "Should restore jobs state"


def test_enable_multiple_jobs(run_jenkee_authed):
    """
    測試批次啟用多個 Jobs

    對應 test plan 步驟 12
    """
    # Arrange: 先停用 jobs
    disable_result = run_jenkee_authed.run(
        "disable-job", "test-job-1", "test-job-2", "--yes-i-really-mean-it"
    )
    assert disable_result.returncode == 0, "Should disable jobs first"

    # Act: 執行 enable-job 指令（批次）
    result = run_jenkee_authed.run(
        "enable-job", "test-job-1", "test-job-2", "--yes-i-really-mean-it"
    )

    # Assert: 驗證執行成功
    assert result.returncode == 0, f"enable-job should succeed, got: {result.stderr}"
    assert "✓" in result.stdout or "success" in result.stdout.lower(), \
        "Should show success message"

    # Verify: 驗證所有 jobs 都被啟用
    status1_result = run_jenkee_authed.run("job-status", "test-job-1")
    status1 = parse_job_status(status1_result.stdout)
    assert status1.status == "ENABLED", "test-job-1 should be enabled"

    status2_result = run_jenkee_authed.run("job-status", "test-job-2")
    status2 = parse_job_status(status2_result.stdout)
    assert status2.status == "ENABLED", "test-job-2 should be enabled"


def test_disable_nonexistent_job(run_jenkee_authed):
    """
    測試停用不存在的 Job

    對應 test plan 錯誤情境測試
    """
    # Arrange: 使用不存在的 job 名稱

    # Act: 執行 disable-job 指令並允許失敗
    result = run_jenkee_authed.build_command(
        "disable-job", "non-existent-job", "--yes-i-really-mean-it"
    ).allow_failure().run()

    # Assert: 驗證失敗
    assert result.returncode != 0, "Should fail for non-existent job"
    error_output = (result.stdout + result.stderr).lower()
    assert 'error' in error_output or 'not found' in error_output or 'no such' in error_output, \
        f"Should have error message, got: {result.stdout + result.stderr}"


# ============================================================================
# 整合測試 - 完整工作流程
# ============================================================================


def test_complete_job_organization_workflow(run_jenkee_authed):
    """
    測試完整的 job 組織工作流程

    對應 test plan 場景 A：組織相關 jobs 到專案 view
    """
    # 1. 列出所有 jobs
    list_result = run_jenkee_authed.run("list-jobs", "--all")
    all_jobs = parse_jobs_list(list_result.stdout)

    assert list_result.returncode == 0, "Step 1: list-jobs should succeed"
    assert len(all_jobs) > 0, "Step 1: Should have at least one job"

    # 2. 批次加入 jobs 到 view（test-view 已經有 job，測試冪等性）
    add_result = run_jenkee_authed.run(
        "add-job-to-view", "test-view", "test-job-1", "test-job-2"
    )

    assert add_result.returncode == 0, "Step 2: add-job-to-view should succeed"

    # 3. 驗證結果
    verify_result = run_jenkee_authed.run("list-jobs", "test-view")
    view_jobs = parse_jobs_list(verify_result.stdout)

    assert verify_result.returncode == 0, "Step 3: list-jobs should succeed"
    assert "test-job-1" in view_jobs, "Step 3: test-job-1 should be in view"
    assert "test-job-2" in view_jobs, "Step 3: test-job-2 should be in view"

    # 4. 查看 jobs 狀態
    for job in ["test-job-1", "test-job-2"]:
        status_result = run_jenkee_authed.run("job-status", job)
        assert status_result.returncode == 0, f"Step 4: job-status should succeed for {job}"


def test_enable_disable_workflow(run_jenkee_authed):
    """
    測試啟用/停用完整流程

    對應 test plan 場景 B：維護期間暫停 jobs
    驗證 enable/disable 是可逆操作
    """
    # 1. 確認初始狀態（啟用）
    initial_status_result = run_jenkee_authed.run("job-status", "test-job-3")
    initial_status = parse_job_status(initial_status_result.stdout)

    # 如果初始是 disabled，先啟用
    if initial_status.status == "DISABLED":
        enable_result = run_jenkee_authed.run(
            "enable-job", "test-job-3", "--yes-i-really-mean-it"
        )
        assert enable_result.returncode == 0, "Should enable job first"

    # 2. 停用 job
    disable_result = run_jenkee_authed.run(
        "disable-job", "test-job-3", "--yes-i-really-mean-it"
    )
    assert disable_result.returncode == 0, "Step 2: disable-job should succeed"

    # 3. 驗證已停用
    disabled_status_result = run_jenkee_authed.run("job-status", "test-job-3")
    disabled_status = parse_job_status(disabled_status_result.stdout)
    assert disabled_status.status == "DISABLED", \
        "Step 3: Job should be disabled"

    # 4. 重新啟用
    enable_result = run_jenkee_authed.run(
        "enable-job", "test-job-3", "--yes-i-really-mean-it"
    )
    assert enable_result.returncode == 0, "Step 4: enable-job should succeed"

    # 5. 驗證已啟用
    enabled_status_result = run_jenkee_authed.run("job-status", "test-job-3")
    enabled_status = parse_job_status(enabled_status_result.stdout)
    assert enabled_status.status == "ENABLED", \
        "Step 5: Job should be enabled"

    # 6. 驗證可以觸發 build
    build_result = run_jenkee_authed.run("build", "test-job-3")
    assert build_result.returncode == 0, \
        "Step 6: Should be able to trigger build after enabling"


def test_job_organization_output_is_parseable(run_jenkee_authed):
    """
    測試 job organization 指令的輸出可以被腳本解析

    確保輸出格式穩定，適合自動化使用
    """
    # Test job-status
    status_result = run_jenkee_authed.run("job-status", "test-job-1")
    status = parse_job_status(status_result.stdout)

    # 應該能夠成功解析
    assert status.name == "test-job-1", "Should be able to parse job-status output"
    assert status.status in ["ENABLED", "DISABLED"], "Should have valid status"

    # Test list-jobs (from view)
    list_result = run_jenkee_authed.run("list-jobs", "test-view")
    jobs = parse_jobs_list(list_result.stdout)

    # 應該能夠成功解析
    assert len(jobs) > 0, "Should be able to parse list-jobs output"
    assert all(isinstance(job, str) for job in jobs), "All jobs should be strings"
