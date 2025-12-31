"""
測試 Build Execution and Monitoring 相關指令

涵蓋指令：
- build: 觸發 job build
- list-builds: 列出 build 歷史
- console: 取得 console 輸出
- stop-builds: 停止執行中的 builds (TODO)
"""
import re
from dataclasses import dataclass
from typing import List, Optional, Set


# ============================================================================
# Parser Functions - 將命令輸出解析為可精確比對的資料結構
# ============================================================================


@dataclass
class BuildResult:
    """Build 指令執行結果的結構化資料"""
    success: bool
    job_name: Optional[str]
    build_number: Optional[int]
    queued: bool
    status: Optional[str]  # SUCCESS, FAILURE, ABORTED, etc.
    raw_output: str


def parse_build_result(stdout: str, stderr: str, returncode: int) -> BuildResult:
    """
    解析 build 命令的輸出

    預期格式範例：
    - Fire-and-forget 模式：
        "✓ Build triggered for job 'test-job-1'"
        或 "Build queued for job: test-job-1"

    - Sync 模式：
        "Build #5 started for job: test-job-1"
        "Build #5 completed: SUCCESS"

    - Follow 模式：
        (包含 console 輸出)
        "Build #5 completed: SUCCESS"

    Returns:
        BuildResult: 結構化的 build 執行結果
    """
    output = stdout + stderr
    success = returncode == 0

    job_name = None
    build_number = None
    queued = False
    status = None

    # 提取 job 名稱（多種格式）
    # 格式1: "job 'test-job-1'"
    job_match = re.search(r"job\s+'([^']+)'", output)
    if not job_match:
        # 格式2: "job: test-job-1"
        job_match = re.search(r'job:\s*(\S+)', output)
    if job_match:
        job_name = job_match.group(1)

    # 提取 build 編號（多種格式）
    # 格式1: "Build #5" 或 "build #5"
    build_match = re.search(r'[Bb]uild\s+#(\d+)', output)
    if not build_match:
        # 格式2: "test-job-1 #5" (job name followed by #number)
        build_match = re.search(r'\S+\s+#(\d+)', output)
    if build_match:
        build_number = int(build_match.group(1))

    # 檢查是否觸發或排入佇列
    if 'triggered' in output.lower() or 'queued' in output.lower() or 'queue' in output.lower():
        queued = True

    # 提取 build 狀態
    status_match = re.search(r'(SUCCESS|FAILURE|UNSTABLE|ABORTED|NOT_BUILT)', output, re.IGNORECASE)
    if status_match:
        status = status_match.group(1).upper()

    return BuildResult(
        success=success,
        job_name=job_name,
        build_number=build_number,
        queued=queued,
        status=status,
        raw_output=output
    )


@dataclass
class BuildInfo:
    """單一 build 的資訊"""
    number: int
    status: str  # SUCCESS, FAILURE, UNSTABLE, ABORTED, etc.
    timestamp: Optional[str] = None
    duration: Optional[str] = None


def parse_builds_list(stdout: str) -> List[BuildInfo]:
    """
    解析 list-builds 命令的輸出

    預期格式（增強版）：
        #5 SUCCESS 2025-12-31 10:00:00 30s
        #4 FAILURE 2025-12-31 09:00:00 45s
        #3 SUCCESS 2025-12-31 08:00:00 28s

    Returns:
        List[BuildInfo]: builds 列表，按編號排序
    """
    builds = []
    lines = stdout.strip().split('\n')

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 跳過錯誤或特殊訊息
        lower_line = line.lower()
        if ('no builds' in lower_line or 'error' in lower_line or
            'not found' in lower_line or '===' in line):
            continue

        # 舊格式：純數字（向後兼容）
        if line.isdigit():
            number = int(line)
            builds.append(BuildInfo(
                number=number,
                status='UNKNOWN',
                timestamp=None,
                duration=None
            ))
            continue

        # 新格式：包含狀態、時間戳、持續時間
        # 提取 build 編號
        number_match = re.search(r'#?(\d+)', line)
        if not number_match:
            continue

        number = int(number_match.group(1))

        # 提取狀態
        status_match = re.search(r'\b(SUCCESS|FAILURE|UNSTABLE|ABORTED|NOT_BUILT|BUILDING)\b', line, re.IGNORECASE)
        status = status_match.group(1).upper() if status_match else 'UNKNOWN'

        # 提取時間戳
        timestamp_match = re.search(r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}', line)
        timestamp = timestamp_match.group(0) if timestamp_match else None

        # 提取持續時間
        duration_match = re.search(r'\d+\.?\d*s', line)
        duration = duration_match.group(0) if duration_match else None

        builds.append(BuildInfo(
            number=number,
            status=status,
            timestamp=timestamp,
            duration=duration
        ))

    return builds


def parse_console_output(stdout: str) -> str:
    """
    解析 console 命令的輸出

    Console 輸出通常是純文字，直接返回清理後的內容

    Returns:
        str: console 輸出內容
    """
    return stdout.strip()


@dataclass
class StopBuildsResult:
    """Stop-builds 指令執行結果的結構化資料"""
    success: bool
    job_names: List[str]
    stopped_count: int
    raw_output: str


def parse_stop_builds_result(stdout: str, stderr: str, returncode: int) -> StopBuildsResult:
    """
    解析 stop-builds 命令的輸出

    預期格式範例：
    - 單一 job：
        "✓ Stopped all running builds for job 'long-running-job'"

    - 多個 jobs：
        "✓ Stopped all running builds for 2 job(s)"
        "  - long-running-job"
        "  - another-job"

    Returns:
        StopBuildsResult: 結構化的 stop-builds 執行結果
    """
    output = stdout + stderr
    success = returncode == 0

    job_names = []
    stopped_count = 0

    # 提取 job 名稱（多種格式）
    # 格式1: "job 'long-running-job'"
    single_job_match = re.search(r"job\s+'([^']+)'", output)
    if single_job_match:
        job_names.append(single_job_match.group(1))
        stopped_count = 1
    else:
        # 格式2: 多個 jobs，從列表中提取
        # "  - job-name"
        job_list_matches = re.findall(r'^\s*-\s+(\S+)', output, re.MULTILINE)
        if job_list_matches:
            job_names.extend(job_list_matches)

        # 嘗試提取停止的 job 數量
        count_match = re.search(r'(\d+)\s+job\(s\)', output)
        if count_match:
            stopped_count = int(count_match.group(1))
        else:
            stopped_count = len(job_names)

    return StopBuildsResult(
        success=success,
        job_names=job_names,
        stopped_count=stopped_count,
        raw_output=output
    )


# ============================================================================
# 測試函數 - Build 指令
# ============================================================================


def test_build_fire_and_forget(run_jenkee_authed):
    """
    測試觸發簡單 Build（Fire-and-Forget 模式）

    對應 test plan 步驟 1
    """
    # Arrange: 使用 test-job-1（由 fixture 建立）

    # Act: 執行 build 指令（預設為 fire-and-forget）
    result = run_jenkee_authed.run("build", "test-job-1")

    # Parse: 解析輸出
    build_result = parse_build_result(result.stdout, result.stderr, result.returncode)

    # Assert: 驗證執行成功
    assert build_result.success, f"Build should succeed, got: {build_result.raw_output}"
    assert build_result.job_name == "test-job-1" or "test-job-1" in build_result.raw_output, \
        "Output should contain job name"
    # Fire-and-forget 模式通常會排入佇列
    assert build_result.queued or build_result.build_number is not None, \
        "Build should be queued or started"


def test_build_sync_mode(run_jenkee_authed):
    """
    測試觸發 Build 並同步等待（Sync 模式）

    對應 test plan 步驟 2
    """
    # Arrange: 使用 test-job-1，並使用 -s 參數

    # Act: 執行 build -s 指令（同步等待）
    result = run_jenkee_authed.run("build", "test-job-1", "-s")

    # Parse: 解析輸出
    build_result = parse_build_result(result.stdout, result.stderr, result.returncode)

    # Assert: 驗證執行成功且有 build 狀態
    assert build_result.success, f"Build should succeed, got: {build_result.raw_output}"
    assert build_result.build_number is not None, "Should have build number in sync mode"
    # 在 sync 模式應該有最終狀態
    assert build_result.status is not None, f"Should have build status, got: {build_result.raw_output}"


def test_build_follow_mode(run_jenkee_authed):
    """
    測試觸發 Build 並追蹤進度（Follow 模式）

    對應 test plan 步驟 3
    """
    # Arrange: 使用 test-job-1，並使用 -f 參數

    # Act: 執行 build -f 指令（追蹤模式）
    result = run_jenkee_authed.run("build", "test-job-1", "-f")

    # Parse: 解析輸出
    build_result = parse_build_result(result.stdout, result.stderr, result.returncode)

    # Assert: 驗證執行成功且有 console 輸出
    assert build_result.success, f"Build should succeed, got: {build_result.raw_output}"
    assert len(build_result.raw_output) > 0, "Should have console output in follow mode"
    # Follow 模式應該包含 build 完成狀態
    assert build_result.status is not None or 'completed' in build_result.raw_output.lower(), \
        f"Should show build completion, got: {build_result.raw_output}"


def test_build_nonexistent_job(run_jenkee_authed):
    """
    測試觸發不存在的 Job

    對應 test plan 錯誤情境測試
    """
    # Arrange: 使用不存在的 job 名稱

    # Act: 執行 build 指令並允許失敗
    result = run_jenkee_authed.build_command("build", "non-existent-job").allow_failure().run()

    # Parse: 解析輸出
    build_result = parse_build_result(result.stdout, result.stderr, result.returncode)

    # Assert: 驗證失敗
    assert not build_result.success, "Should fail for non-existent job"
    assert result.returncode != 0, "Should have non-zero exit code"
    # 錯誤訊息應包含相關資訊
    error_output = (result.stdout + result.stderr).lower()
    assert 'error' in error_output or 'not found' in error_output or 'does not exist' in error_output, \
        f"Should have error message, got: {result.stdout + result.stderr}"


# ============================================================================
# 測試函數 - List-Builds 指令
# ============================================================================


def test_list_builds_basic(run_jenkee_authed):
    """
    測試列出 Build 歷史

    對應 test plan 步驟 5
    """
    # Arrange: test-job-1 應該已經有一些 builds（由 fixture 或前面的測試觸發）
    # 先確保至少有一個 build
    run_jenkee_authed.run("build", "test-job-1", "-s")

    # Act: 執行 list-builds 指令
    result = run_jenkee_authed.run("list-builds", "test-job-1")

    # Parse: 解析輸出
    builds = parse_builds_list(result.stdout)

    # Assert: 驗證執行成功
    assert result.returncode == 0, f"list-builds should succeed, got: {result.stderr}"
    assert len(builds) > 0, f"Should have at least one build. Output was: {result.stdout}"

    # 驗證 build 資訊格式
    for build in builds:
        assert build.number > 0, f"Build number should be positive, got {build.number}"
        # 驗證 status 應該是已知的 Jenkins build 狀態
        valid_statuses = {'SUCCESS', 'FAILURE', 'UNSTABLE', 'ABORTED', 'NOT_BUILT', 'BUILDING'}
        assert build.status in valid_statuses, \
            f"Build status should be one of {valid_statuses}, got {build.status}"
        # 驗證時間戳格式（應該存在）
        assert build.timestamp is not None, f"Build should have timestamp"
        # 驗證持續時間格式（應該存在）
        assert build.duration is not None, f"Build should have duration"


def test_list_builds_nonexistent_job(run_jenkee_authed):
    """
    測試列出不存在 Job 的 Builds

    對應 test plan 錯誤情境測試
    """
    # Arrange: 使用不存在的 job 名稱

    # Act: 執行 list-builds 指令並允許失敗
    result = run_jenkee_authed.build_command("list-builds", "non-existent-job").allow_failure().run()

    # Assert: 驗證失敗
    assert result.returncode != 0, "Should fail for non-existent job"
    error_output = (result.stdout + result.stderr).lower()
    assert 'error' in error_output or 'not found' in error_output or 'does not exist' in error_output, \
        f"Should have error message, got: {result.stdout + result.stderr}"


# ============================================================================
# 測試函數 - Console 指令
# ============================================================================


def test_console_latest_build(run_jenkee_authed):
    """
    測試取得最新 Build 的 Console 輸出

    對應 test plan 步驟 7
    """
    # Arrange: 先觸發一個 build 並等待完成
    run_jenkee_authed.run("build", "test-job-1", "-s")

    # Act: 執行 console 指令（不指定 build 編號，取得最新的）
    result = run_jenkee_authed.run("console", "test-job-1")

    # Parse: 解析輸出
    console_output = parse_console_output(result.stdout)

    # Assert: 驗證執行成功
    assert result.returncode == 0, "console should succeed"
    assert len(console_output) > 0, "Console output should not be empty"
    # Console 輸出通常包含 Jenkins 相關訊息
    # 這裡只做基本檢查，因為不同的 job 輸出格式會不同


def test_console_specific_build(run_jenkee_authed):
    """
    測試取得特定 Build 的 Console 輸出

    對應 test plan 步驟 8
    """
    # Arrange: 先觸發一個 build 並等待完成
    run_jenkee_authed.run("build", "test-job-1", "-s")

    # 取得最新的 build 編號
    list_result = run_jenkee_authed.run("list-builds", "test-job-1")
    builds = parse_builds_list(list_result.stdout)
    assert len(builds) > 0, "Should have at least one build"
    # 取得最新的 build（Jenkins 返回的 builds 通常是從新到舊）
    build_number = builds[0].number

    # Act: 執行 console 指令，指定 build 編號
    result = run_jenkee_authed.run("console", "test-job-1", str(build_number))

    # Parse: 解析輸出
    console_output = parse_console_output(result.stdout)

    # Assert: 驗證執行成功
    assert result.returncode == 0, f"console should succeed for build #{build_number}"
    assert len(console_output) > 0, "Console output should not be empty"


def test_console_nonexistent_build(run_jenkee_authed):
    """
    測試查詢不存在的 Build

    對應 test plan 錯誤情境測試
    """
    # Arrange: 使用一個非常大的 build 編號（應該不存在）

    # Act: 執行 console 指令並允許失敗
    result = run_jenkee_authed.build_command("console", "test-job-1", "99999").allow_failure().run()

    # Assert: 驗證失敗
    assert result.returncode != 0, "Should fail for non-existent build"
    error_output = (result.stdout + result.stderr).lower()
    assert 'error' in error_output or 'not found' in error_output or 'does not exist' in error_output, \
        f"Should have error message, got: {result.stdout + result.stderr}"


# ============================================================================
# 整合測試 - 完整工作流程
# ============================================================================


def test_complete_build_workflow(run_jenkee_authed):
    """
    測試完整的 build 執行與監控工作流程

    對應 test plan 場景 A：觸發 build 並監控結果
    """
    # 1. 觸發 build（fire-and-forget）
    build_result = run_jenkee_authed.run("build", "test-job-1")
    assert build_result.returncode == 0, "Build should be queued successfully"

    # 2. 等待 build 完成（使用 sync 模式重新觸發）
    sync_result = run_jenkee_authed.run("build", "test-job-1", "-s")
    assert sync_result.returncode == 0, "Build should complete successfully"

    # 3. 查看 build 歷史
    list_result = run_jenkee_authed.run("list-builds", "test-job-1")
    builds = parse_builds_list(list_result.stdout)
    assert len(builds) > 0, "Should have builds in history"

    # 4. 查看最新 build 的 console 輸出
    console_result = run_jenkee_authed.run("console", "test-job-1")
    console_output = parse_console_output(console_result.stdout)
    assert len(console_output) > 0, "Should have console output"

    # 5. 驗證整個流程順利完成
    assert True, "Complete build workflow executed successfully"


# ============================================================================
# 測試函數 - Stop-Builds 指令
# ============================================================================


def test_stop_builds_basic(run_jenkee_authed):
    """
    測試停止執行中的 Builds

    對應 test plan 步驟 8
    """
    import time
    import subprocess

    # Arrange: 先觸發一個長時間執行的 build（不等待完成）
    # 使用 fire-and-forget 模式，這樣它會開始執行但不會阻塞
    trigger_result = run_jenkee_authed.run("build", "long-running-job")
    assert trigger_result.returncode == 0, "Should trigger build successfully"

    # 等待一小段時間讓 build 開始執行（避免還在 queue 中）
    time.sleep(3)

    # Act: 執行 stop-builds 指令
    result = run_jenkee_authed.run("stop-builds", "long-running-job")

    # Parse: 解析輸出
    stop_result = parse_stop_builds_result(result.stdout, result.stderr, result.returncode)

    # Assert: 驗證執行成功
    assert stop_result.success, f"stop-builds should succeed, got: {stop_result.raw_output}"
    assert "long-running-job" in stop_result.job_names or "long-running-job" in stop_result.raw_output, \
        f"Should reference the job name, got: {stop_result.raw_output}"


def test_verify_stopped_build_status(run_jenkee_authed):
    """
    測試驗證停止的 Build 狀態

    對應 test plan 步驟 9
    """
    import time

    # Arrange: 先觸發一個長時間執行的 build
    trigger_result = run_jenkee_authed.run("build", "long-running-job")
    assert trigger_result.returncode == 0, "Should trigger build successfully"

    # 等待 build 開始執行
    time.sleep(3)

    # Act: 停止 build
    stop_result = run_jenkee_authed.run("stop-builds", "long-running-job")
    assert stop_result.returncode == 0, "Should stop build successfully"

    # 等待一小段時間讓 Jenkins 更新狀態
    time.sleep(2)

    # 驗證：查看 build 歷史
    list_result = run_jenkee_authed.run("list-builds", "long-running-job")
    builds = parse_builds_list(list_result.stdout)

    # Assert: 驗證最新的 build 狀態為 ABORTED
    assert len(builds) > 0, "Should have at least one build"

    # 找出最新的 build（編號最大的）
    latest_build = max(builds, key=lambda b: b.number)

    # 驗證狀態為 ABORTED（可能需要等待一段時間讓狀態更新）
    # 如果狀態還是 BUILDING，再等一下
    if latest_build.status == 'BUILDING':
        time.sleep(2)
        list_result = run_jenkee_authed.run("list-builds", "long-running-job")
        builds = parse_builds_list(list_result.stdout)
        latest_build = max(builds, key=lambda b: b.number)

    assert latest_build.status == 'ABORTED', \
        f"Latest build should be ABORTED, got {latest_build.status}"


def test_stop_builds_nonexistent_job(run_jenkee_authed):
    """
    測試停止不存在 Job 的 Builds

    對應 test plan 錯誤情境測試
    """
    # Arrange: 使用不存在的 job 名稱

    # Act: 執行 stop-builds 指令並允許失敗
    result = run_jenkee_authed.build_command("stop-builds", "non-existent-job").allow_failure().run()

    # Assert: 驗證失敗
    assert result.returncode != 0, "Should fail for non-existent job"
    error_output = (result.stdout + result.stderr).lower()
    assert 'error' in error_output or 'not found' in error_output or 'does not exist' in error_output, \
        f"Should have error message, got: {result.stdout + result.stderr}"


def test_stop_builds_no_running_builds(run_jenkee_authed):
    """
    測試停止沒有執行中 Builds 的 Job

    對應 test plan 錯誤情境測試
    """
    # Arrange: 使用一個確定沒有執行中 builds 的 job
    # test-job-1 通常是空的快速 job，應該不會有執行中的 builds

    # Act: 執行 stop-builds 指令
    # 這個操作應該成功，但可能沒有實際停止任何 build
    result = run_jenkee_authed.run("stop-builds", "test-job-1")

    # Parse: 解析輸出
    stop_result = parse_stop_builds_result(result.stdout, result.stderr, result.returncode)

    # Assert: 驗證執行成功（即使沒有 builds 需要停止）
    assert stop_result.success, f"stop-builds should succeed even with no running builds"
