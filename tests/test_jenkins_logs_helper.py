"""Helper test to view Jenkins logs and init script execution results"""


def test_view_jenkins_init_output(jenkins_instance):
    """
    查看 Jenkins 初始化輸出（包含 fixture scripts 的執行結果）

    這個測試主要用於 debug 和驗證 fixture scripts 是否正確執行。
    執行時使用 -s flag 來查看輸出：pytest tests/test_jenkins_logs_helper.py::test_view_jenkins_init_output -s
    """
    # 方式 1：取得分離的 stdout 和 stderr
    stdout, stderr = jenkins_instance.get_logs()

    # 方式 2：取得合併的 logs（不標示 stream）
    combined_logs = jenkins_instance.get_logs_combined()

    # 方式 3：取得合併的 logs（標示 stdout/stderr）
    combined_logs_marked = jenkins_instance.get_logs_combined(mark_streams=True)

    print("\n" + "=" * 80)
    print("Jenkins Init Scripts Execution Output")
    print("=" * 80)

    # 過濾出我們關心的訊息
    for line in combined_logs.split('\n'):
        if any(keyword in line for keyword in [
            'Created job',
            'Created view',
            'Added',
            'Verification',
            'Test jobs and views setup completed',
            'GroovyHookScript#execute',
            '01-create-test-jobs.groovy'
        ]):
            print(line)

    print("=" * 80)

    # 驗證關鍵訊息存在
    assert 'Created job: test-job-1' in combined_logs
    assert 'Created job: test-job-2' in combined_logs
    assert 'Created job: test-job-3' in combined_logs
    assert 'Created view: test-view' in combined_logs
    assert 'Created empty view: empty-view' in combined_logs


def test_separate_stdout_stderr(jenkins_instance):
    """
    示範如何分別取得 stdout 和 stderr

    有時候需要分別查看 stdout 和 stderr 來除錯。
    """
    stdout, stderr = jenkins_instance.get_logs()

    # 處理可能是 bytes 或 str 的情況
    stdout_text = stdout.decode('utf-8', errors='ignore') if isinstance(stdout, bytes) else stdout
    stderr_text = stderr.decode('utf-8', errors='ignore') if isinstance(stderr, bytes) else stderr

    print("\n=== STDOUT ===")
    print(f"Length: {len(stdout_text)} characters")

    print("\n=== STDERR ===")
    print(f"Length: {len(stderr_text)} characters")

    # Jenkins 的主要輸出通常在 stdout
    assert len(stdout_text) > 0 or len(stderr_text) > 0, "Should have some logs"
