"""
測試 Advanced Operations 相關指令

涵蓋指令：
- groovy: 執行 Groovy script

測試重點：
- 執行簡單的 Groovy script
- 使用 script 查詢 Jenkins 資訊
- 從檔案載入 script
- 錯誤處理與安全性驗證
"""
from dataclasses import dataclass
from pathlib import Path


# ============================================================================
# Parser Functions - 將命令輸出解析為可精確比對的資料結構
# ============================================================================


@dataclass
class GroovyOutput:
    """Groovy script 輸出的結構化資料"""
    stdout: str
    stderr: str
    success: bool
    lines: list[str]

    @property
    def first_line(self) -> str:
        """取得第一行輸出（如果有的話）"""
        return self.lines[0] if self.lines else ""


def parse_groovy_output(result) -> GroovyOutput:
    """
    解析 groovy 命令的輸出

    預期格式：
        - stdout: script 的 println 輸出（每行一個結果）
        - stderr: 錯誤訊息（如果有）
        - returncode: 0 表示成功

    範例輸出：
        Hello from Groovy
        Line 2
        Line 3

    Returns:
        GroovyOutput: 結構化的輸出資料
    """
    stdout = result.stdout.strip()
    stderr = result.stderr.strip()
    success = result.returncode == 0

    # 將輸出分割成行，過濾空行
    lines = [line.strip() for line in stdout.split('\n') if line.strip()]

    return GroovyOutput(
        stdout=stdout,
        stderr=stderr,
        success=success,
        lines=lines
    )


# ============================================================================
# 測試函數 - 基本 Groovy 執行
# ============================================================================


def test_groovy_simple_hello(run_jenkee_authed, tmp_path):
    """
    測試執行簡單的 Hello World script

    對應 test plan 步驟 1
    """
    # Arrange: 準備簡單的 Hello World script
    script = "println('Hello from Groovy')"
    script_file = tmp_path / "hello.groovy"
    script_file.write_text(script)

    # Act: 執行 groovy 指令
    result = run_jenkee_authed.run(
        "groovy", str(script_file), "--yes-i-really-mean-it"
    )

    # Parse: 解析輸出
    output = parse_groovy_output(result)

    # Assert: 驗證執行成功
    assert result.returncode == 0, f"groovy should succeed, got: {result.stderr}"
    assert output.success, "Script execution should succeed"

    # Verify: 驗證輸出內容
    assert "Hello from Groovy" in output.stdout, \
        f"Expected 'Hello from Groovy' in output, got: {output.stdout}"


def test_groovy_with_confirmation_cancelled(run_jenkee_authed, tmp_path):
    """
    測試取消執行 Groovy script（模擬輸入 n）

    對應文件中的「測試 2: 取消執行」
    """
    # Arrange: 準備簡單的 script
    script = "println('Hello from Groovy')"
    script_file = tmp_path / "hello-cancel.groovy"
    script_file.write_text(script)

    # Act: 嘗試執行但取消（模擬輸入 'n'）
    result = run_jenkee_authed.build_command(
        "groovy", str(script_file)
    ).with_stdin("n\n").run()

    # Assert: 驗證返回 0（取消不是錯誤）
    assert result.returncode == 0, f"Should return 0 when cancelled, got: {result.returncode}"
    assert "cancelled" in result.stdout.lower() or "canceled" in result.stdout.lower(), \
        "Should show cancellation message"


def test_groovy_with_confirmation_confirmed(run_jenkee_authed, tmp_path):
    """
    測試互動式確認後執行 Groovy script（模擬輸入 y）

    對應文件中的「測試 1: 互動式確認」
    """
    # Arrange: 準備簡單的 script
    script = "println('Hello from Groovy')"
    script_file = tmp_path / "hello-confirm.groovy"
    script_file.write_text(script)

    # Act: 執行並確認（模擬輸入 'y'）
    result = run_jenkee_authed.build_command(
        "groovy", str(script_file)
    ).with_stdin("y\n").run()

    # Assert: 驗證執行成功
    assert result.returncode == 0, f"groovy should succeed, got: {result.stderr}"
    assert "Hello from Groovy" in result.stdout, \
        "Should show groovy script output after confirmation"


def test_groovy_jenkins_version(run_jenkee_authed, tmp_path):
    """
    測試查詢 Jenkins 版本

    對應 test plan 步驟 2
    """
    # Arrange: 準備查詢版本的 script
    script = """
import jenkins.model.Jenkins
println(Jenkins.instance.version)
"""
    script_file = tmp_path / "version.groovy"
    script_file.write_text(script)

    # Act: 執行 groovy 指令
    result = run_jenkee_authed.run(
        "groovy", str(script_file), "--yes-i-really-mean-it"
    )

    # Parse: 解析輸出
    output = parse_groovy_output(result)

    # Assert: 驗證執行成功
    assert result.returncode == 0, f"groovy should succeed, got: {result.stderr}"
    assert output.success, "Script execution should succeed"

    # Verify: 驗證輸出是版本號格式（例如：2.440.1）
    version = output.first_line
    assert version, "Version should not be empty"
    # 驗證版本號格式（至少有數字和點）
    assert any(c.isdigit() for c in version), \
        f"Version should contain digits, got: {version}"


def test_groovy_list_jobs(run_jenkee_authed, tmp_path):
    """
    測試列出所有 Jobs

    對應 test plan 步驟 3
    """
    # Arrange: 準備列出 jobs 的 script
    script = """
import jenkins.model.Jenkins
Jenkins.instance.items.each { job ->
    println(job.name)
}
"""
    script_file = tmp_path / "list-jobs.groovy"
    script_file.write_text(script)

    # Act: 執行 groovy 指令
    result = run_jenkee_authed.run(
        "groovy", str(script_file), "--yes-i-really-mean-it"
    )

    # Parse: 解析輸出
    output = parse_groovy_output(result)

    # Assert: 驗證執行成功
    assert result.returncode == 0, f"groovy should succeed, got: {result.stderr}"
    assert output.success, "Script execution should succeed"

    # Verify: 驗證至少列出了一些 jobs（測試環境有 test-job-1, test-job-2, test-job-3）
    job_names = set(output.lines)
    expected_jobs = {"test-job-1", "test-job-2", "test-job-3"}
    assert expected_jobs.issubset(job_names), \
        f"Expected {expected_jobs} to be in {job_names}"


def test_groovy_job_count(run_jenkee_authed, tmp_path):
    """
    測試計算 Jobs 數量

    對應 test plan 步驟 4
    """
    # Arrange: 準備計算 jobs 數量的 script
    script = """
import jenkins.model.Jenkins
println(Jenkins.instance.items.size())
"""
    script_file = tmp_path / "count-jobs.groovy"
    script_file.write_text(script)

    # Act: 執行 groovy 指令
    result = run_jenkee_authed.run(
        "groovy", str(script_file), "--yes-i-really-mean-it"
    )

    # Parse: 解析輸出
    output = parse_groovy_output(result)

    # Assert: 驗證執行成功
    assert result.returncode == 0, f"groovy should succeed, got: {result.stderr}"
    assert output.success, "Script execution should succeed"

    # Verify: 驗證輸出是數字且大於 0
    count = output.first_line
    assert count.isdigit(), f"Count should be a number, got: {count}"
    assert int(count) >= 3, f"Should have at least 3 jobs, got: {count}"


def test_groovy_multiline_script(run_jenkee_authed, tmp_path):
    """
    測試執行多行 script

    對應 test plan 步驟 6
    """
    # Arrange: 準備多行 script
    script = """
import jenkins.model.Jenkins

def jenkins = Jenkins.instance

println("=== Jenkins Statistics ===")
println("Version: ${jenkins.version}")
println("Total Jobs: ${jenkins.items.size()}")
"""
    script_file = tmp_path / "multiline.groovy"
    script_file.write_text(script)

    # Act: 執行 groovy 指令
    result = run_jenkee_authed.run(
        "groovy", str(script_file), "--yes-i-really-mean-it"
    )

    # Parse: 解析輸出
    output = parse_groovy_output(result)

    # Assert: 驗證執行成功
    assert result.returncode == 0, f"groovy should succeed, got: {result.stderr}"
    assert output.success, "Script execution should succeed"

    # Verify: 驗證輸出包含預期的標題和內容
    assert "=== Jenkins Statistics ===" in output.stdout, \
        "Should contain statistics header"
    assert "Version:" in output.stdout, "Should contain version info"
    assert "Total Jobs:" in output.stdout, "Should contain job count"


def test_groovy_query_specific_job(run_jenkee_authed, tmp_path):
    """
    測試查詢特定 Job 的資訊

    對應 test plan 步驟 5
    """
    # Arrange: 準備查詢特定 job 的 script
    script = """
import jenkins.model.Jenkins

def job = Jenkins.instance.getItem("test-job-1")
if (job != null) {
    println("Job: ${job.name}")
    println("Enabled: ${!job.isDisabled()}")
    println("Buildable: ${job.isBuildable()}")
} else {
    println("Job not found")
}
"""
    script_file = tmp_path / "query-job.groovy"
    script_file.write_text(script)

    # Act: 執行 groovy 指令
    result = run_jenkee_authed.run(
        "groovy", str(script_file), "--yes-i-really-mean-it"
    )

    # Parse: 解析輸出
    output = parse_groovy_output(result)

    # Assert: 驗證執行成功
    assert result.returncode == 0, f"groovy should succeed, got: {result.stderr}"
    assert output.success, "Script execution should succeed"

    # Verify: 驗證輸出包含 job 資訊
    assert "Job: test-job-1" in output.stdout, "Should contain job name"
    assert "Enabled:" in output.stdout, "Should contain enabled status"
    assert "Buildable:" in output.stdout, "Should contain buildable status"


# ============================================================================
# 測試函數 - 錯誤情境
# ============================================================================


def test_groovy_syntax_error(run_jenkee_authed, tmp_path):
    """
    測試執行有語法錯誤的 script

    對應 test plan 錯誤情境測試
    """
    # Arrange: 準備有語法錯誤的 script
    script = "invalid groovy syntax {"
    script_file = tmp_path / "invalid.groovy"
    script_file.write_text(script)

    # Act: 執行 groovy 指令並允許失敗
    result = run_jenkee_authed.build_command(
        "groovy", str(script_file), "--yes-i-really-mean-it"
    ).allow_failure().run()

    # Parse: 解析輸出
    output = parse_groovy_output(result)

    # Assert: 驗證失敗
    assert result.returncode != 0, "Should fail with syntax error"
    assert not output.success, "Script execution should fail"

    # Verify: 驗證錯誤訊息（可能在 stdout 或 stderr）
    error_output = (result.stdout + result.stderr).lower()
    # Jenkins groovy console 可能會在 stdout 或 stderr 顯示錯誤
    assert 'error' in error_output or 'exception' in error_output or 'unexpected' in error_output, \
        f"Should have error message, got stdout: {result.stdout}, stderr: {result.stderr}"


def test_groovy_null_handling(run_jenkee_authed, tmp_path):
    """
    測試存取不存在的 Job（null 處理）

    對應 test plan 錯誤情境測試
    """
    # Arrange: 準備查詢不存在 job 的 script（包含 null 檢查）
    script = """
import jenkins.model.Jenkins

def job = Jenkins.instance.getItem("non-existent-job")
if (job == null) {
    println("Job not found")
} else {
    println("Job found: ${job.name}")
}
"""
    script_file = tmp_path / "null-check.groovy"
    script_file.write_text(script)

    # Act: 執行 groovy 指令
    result = run_jenkee_authed.run(
        "groovy", str(script_file), "--yes-i-really-mean-it"
    )

    # Parse: 解析輸出
    output = parse_groovy_output(result)

    # Assert: 驗證執行成功（script 本身沒問題，只是 job 不存在）
    assert result.returncode == 0, f"groovy should succeed, got: {result.stderr}"
    assert output.success, "Script execution should succeed"

    # Verify: 驗證正確處理 null
    assert "Job not found" in output.stdout, \
        f"Should handle null correctly, got: {output.stdout}"


def test_groovy_empty_script(run_jenkee_authed, tmp_path):
    """
    測試執行空的 script

    對應 test plan 錯誤情境測試
    """
    # Arrange: 準備空的 script
    script = ""
    script_file = tmp_path / "empty.groovy"
    script_file.write_text(script)

    # Act: 執行 groovy 指令並允許失敗
    result = run_jenkee_authed.build_command(
        "groovy", str(script_file), "--yes-i-really-mean-it"
    ).allow_failure().run()

    # Assert: 驗證失敗（empty script 應該被拒絕）
    assert result.returncode != 0, "Should fail with empty script"

    # Verify: 驗證錯誤訊息
    error_output = (result.stdout + result.stderr).lower()
    assert 'error' in error_output or 'empty' in error_output, \
        f"Should have error about empty script, got: {result.stdout + result.stderr}"


def test_groovy_nonexistent_file(run_jenkee_authed, tmp_path):
    """
    測試執行不存在的 script 檔案

    對應 test plan 錯誤情境測試
    """
    # Arrange: 使用不存在的檔案路徑
    script_file = tmp_path / "nonexistent.groovy"

    # Act: 執行 groovy 指令並允許失敗
    result = run_jenkee_authed.build_command(
        "groovy", str(script_file), "--yes-i-really-mean-it"
    ).allow_failure().run()

    # Assert: 驗證失敗
    assert result.returncode != 0, "Should fail when file doesn't exist"

    # Verify: 驗證錯誤訊息
    error_output = (result.stdout + result.stderr).lower()
    assert 'error' in error_output or 'not found' in error_output or 'no such' in error_output, \
        f"Should have error about missing file, got: {result.stdout + result.stderr}"


# ============================================================================
# 測試函數 - 安全性與只讀操作
# ============================================================================


def test_groovy_read_only_operations(run_jenkee_authed, tmp_path):
    """
    測試只讀操作（查詢資訊不修改）

    驗證可以安全執行查詢操作
    """
    # Arrange: 準備只讀的查詢 script
    script = """
import jenkins.model.Jenkins

def jenkins = Jenkins.instance

// 只讀操作：查詢資訊
println("URL: ${jenkins.rootUrl ?: 'Not set'}")
println("Version: ${jenkins.version}")
println("Jobs: ${jenkins.items.size()}")
println("Nodes: ${jenkins.nodes.size() + 1}")  // +1 for master
"""
    script_file = tmp_path / "read-only.groovy"
    script_file.write_text(script)

    # Act: 執行 groovy 指令
    result = run_jenkee_authed.run(
        "groovy", str(script_file), "--yes-i-really-mean-it"
    )

    # Parse: 解析輸出
    output = parse_groovy_output(result)

    # Assert: 驗證執行成功
    assert result.returncode == 0, f"groovy should succeed, got: {result.stderr}"
    assert output.success, "Script execution should succeed"

    # Verify: 驗證輸出包含所有查詢項目
    assert "URL:" in output.stdout, "Should contain URL info"
    assert "Version:" in output.stdout, "Should contain version info"
    assert "Jobs:" in output.stdout, "Should contain jobs count"
    assert "Nodes:" in output.stdout, "Should contain nodes count"


# ============================================================================
# 測試函數 - Dry-Run 模式範例
# ============================================================================


def test_groovy_dry_run_mode(run_jenkee_authed, tmp_path):
    """
    測試 Dry-Run 模式（不實際修改）

    對應 test plan 步驟 7
    """
    # Arrange: 準備 dry-run 模式的 script
    script = """
import jenkins.model.Jenkins

def dryRun = true  // 設為 true，不實際執行

Jenkins.instance.items.findAll { it.disabled }.each { job ->
    if (dryRun) {
        println("[DRY-RUN] Would enable job: ${job.name}")
    } else {
        job.enable()
        println("[EXECUTED] Enabled job: ${job.name}")
    }
}

if (dryRun) {
    println("This was a dry-run.")
}
"""
    script_file = tmp_path / "dry-run.groovy"
    script_file.write_text(script)

    # Act: 執行 groovy 指令
    result = run_jenkee_authed.run(
        "groovy", str(script_file), "--yes-i-really-mean-it"
    )

    # Parse: 解析輸出
    output = parse_groovy_output(result)

    # Assert: 驗證執行成功
    assert result.returncode == 0, f"groovy should succeed, got: {result.stderr}"
    assert output.success, "Script execution should succeed"

    # Verify: 驗證是 dry-run 模式
    assert "This was a dry-run." in output.stdout, \
        "Should indicate dry-run mode"

    # Verify: 確認沒有實際執行（沒有 EXECUTED 訊息）
    assert "[EXECUTED]" not in output.stdout, \
        "Should not have executed any actual changes"


# ============================================================================
# 整合測試 - 完整工作流程
# ============================================================================


def test_groovy_batch_query_workflow(run_jenkee_authed, tmp_path):
    """
    測試完整的批次查詢工作流程

    對應 test plan 場景 A
    """
    # Arrange: 準備批次查詢 script
    script = """
import jenkins.model.Jenkins

def jenkins = Jenkins.instance

println("=== Jenkins Summary ===")
println("Version: ${jenkins.version}")
println("Total Jobs: ${jenkins.items.size()}")

println("")
println("=== Job List ===")
jenkins.items.each { job ->
    def lastBuild = job.lastBuild
    def status = lastBuild ? lastBuild.result : "Never built"
    println("${job.name}: ${status}")
}
"""
    script_file = tmp_path / "batch-query.groovy"
    script_file.write_text(script)

    # Act: 執行 groovy 指令
    result = run_jenkee_authed.run(
        "groovy", str(script_file), "--yes-i-really-mean-it"
    )

    # Parse: 解析輸出
    output = parse_groovy_output(result)

    # Assert: 驗證執行成功
    assert result.returncode == 0, f"groovy should succeed, got: {result.stderr}"
    assert output.success, "Script execution should succeed"

    # Verify: 驗證輸出結構完整
    assert "=== Jenkins Summary ===" in output.stdout, \
        "Should contain summary section"
    assert "=== Job List ===" in output.stdout, \
        "Should contain job list section"
    assert "Version:" in output.stdout, "Should contain version"
    assert "Total Jobs:" in output.stdout, "Should contain job count"

    # Verify: 驗證至少列出了測試 jobs
    assert "test-job-1" in output.stdout, "Should list test-job-1"
    assert "test-job-2" in output.stdout, "Should list test-job-2"
