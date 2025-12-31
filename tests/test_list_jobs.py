"""測試 list-jobs 命令"""


def parse_job_list(output: str) -> set[str]:
    """
    解析 list-jobs 命令的輸出，取得 job 名稱列表

    Args:
        output: list-jobs 命令的 stdout

    Returns:
        set[str]: job 名稱的集合
    """
    # 過濾空行和特殊訊息
    lines = output.strip().split('\n')
    jobs = set()
    for line in lines:
        line = line.strip()
        # 跳過空行和錯誤訊息
        if line and not line.startswith('No jobs found') and not line.startswith('Error'):
            jobs.add(line)
    return jobs


def test_list_jobs_all(run_jenkee_authed):
    """測試列出所有 Jobs（使用 --all）"""
    # Arrange: 透過 run_jenkee_authed 確保已認證且 Jenkins 已啟動
    # 初始化腳本 01-create-test-jobs.groovy 應該已經建立了測試 Job
    # 注意：其他測試可能會建立額外的 jobs

    # Act: 執行 list-jobs --all 指令
    result = run_jenkee_authed.run("list-jobs", "--all")

    # Assert: 驗證執行成功且至少包含初始的 jobs
    assert result.returncode == 0

    jobs = parse_job_list(result.stdout)
    expected_jobs = {"test-job-1", "test-job-2", "test-job-3", "long-running-job"}

    # 使用 issubset 而非精確相等，因為其他測試可能會建立更多 jobs
    assert expected_jobs.issubset(jobs), \
        f"Expected at least {expected_jobs}, but got {jobs}"


def test_list_jobs_all_short_flag(run_jenkee_authed):
    """測試列出所有 Jobs（使用 -a 簡寫）"""
    # Arrange: 透過 run_jenkee_authed 確保已認證且 Jenkins 已啟動
    # 注意：其他測試可能會建立額外的 jobs

    # Act: 執行 list-jobs -a 指令
    result = run_jenkee_authed.run("list-jobs", "-a")

    # Assert: 驗證執行成功且至少包含初始的 jobs
    assert result.returncode == 0

    jobs = parse_job_list(result.stdout)
    expected_jobs = {"test-job-1", "test-job-2", "test-job-3", "long-running-job"}

    # 使用 issubset 而非精確相等，因為其他測試可能會建立更多 jobs
    assert expected_jobs.issubset(jobs), \
        f"Expected at least {expected_jobs}, but got {jobs}"


def test_list_jobs_specific_view(run_jenkee_authed):
    """測試列出特定 View 中的 Jobs"""
    # Arrange: 初始化腳本應該已經建立 test-view 並加入 test-job-1 和 test-job-2
    # 注意：其他測試可能會加入更多 jobs 到 test-view

    # Act: 執行 list-jobs test-view 指令
    result = run_jenkee_authed.run("list-jobs", "test-view")

    # Assert: 驗證執行成功且至少包含初始的 jobs
    assert result.returncode == 0

    jobs = parse_job_list(result.stdout)
    expected_jobs = {"test-job-1", "test-job-2"}

    # 使用 issubset 而非精確相等，因為其他測試可能會加入更多 jobs
    assert expected_jobs.issubset(jobs), \
        f"Expected at least {expected_jobs}, but got {jobs}"


def test_list_jobs_empty_view(run_jenkee_authed):
    """測試列出空 View 的結果"""
    # Arrange: 初始化腳本應該已經建立 empty-view（無 jobs）

    # Act: 執行 list-jobs empty-view 指令
    result = run_jenkee_authed.run("list-jobs", "empty-view")

    # Assert: 驗證執行成功且 job 列表為空
    assert result.returncode == 0

    jobs = parse_job_list(result.stdout)
    expected_jobs = set()

    assert jobs == expected_jobs, f"Expected empty set, but got {jobs}"


def test_list_jobs_missing_argument(run_jenkee_authed):
    """測試缺少參數時的錯誤處理"""
    # Arrange: 不提供任何參數

    # Act: 執行 list-jobs 指令（無參數），允許失敗
    result = run_jenkee_authed.build_command("list-jobs").allow_failure().run()

    # Assert: 驗證返回錯誤
    assert result.returncode != 0
    # 可能包含使用說明或錯誤訊息
    assert "Usage" in result.stderr or "Error" in result.stderr or "usage" in result.stdout.lower()
