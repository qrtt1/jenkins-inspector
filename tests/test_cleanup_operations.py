"""
測試 Cleanup Operations 相關指令

涵蓋指令：
- delete-builds: 刪除 build 記錄
- delete-job: 刪除 jobs

測試重點：
- 刪除單一與批次 builds
- 刪除單一與批次 jobs
- 驗證刪除操作
- 錯誤處理

⚠️ 警告：這些測試會執行實際的刪除操作
"""
from dataclasses import dataclass
from typing import Set, List
import xml.etree.ElementTree as ET


# ============================================================================
# Parser Functions - 將命令輸出解析為可精確比對的資料結構
# ============================================================================


@dataclass
class BuildList:
    """Build 列表的結構化資料"""
    build_numbers: Set[int]

    @property
    def count(self) -> int:
        """取得 build 總數"""
        return len(self.build_numbers)

    def contains(self, build_number: int) -> bool:
        """檢查是否包含特定 build"""
        return build_number in self.build_numbers


def parse_build_list(stdout: str) -> BuildList:
    """
    解析 list-builds 命令的輸出

    預期格式：
        #1 - SUCCESS - 2025-01-01 10:00:00 - 5.2s
        #2 - FAILURE - 2025-01-01 11:00:00 - 3.1s
        #3 - SUCCESS - 2025-01-01 12:00:00 - 4.8s

    或簡單格式（只有編號）：
        #1
        #2
        #3

    Returns:
        BuildList: 包含 build 編號集合的結構化資料
    """
    build_numbers = set()

    for line in stdout.strip().split('\n'):
        line = line.strip()
        if not line:
            continue

        # 找出 #<number> 格式的 build 編號
        if line.startswith('#'):
            # 取第一個詞（#1, #2, 等）
            build_str = line.split()[0]
            try:
                # 去掉 # 號並轉為整數
                build_num = int(build_str[1:])
                build_numbers.add(build_num)
            except (ValueError, IndexError):
                # 如果解析失敗，跳過這行
                continue

    return BuildList(build_numbers=build_numbers)


def parse_job_list(stdout: str) -> Set[str]:
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
        if line:
            jobs.add(line)

    return jobs


# ============================================================================
# Helper Functions
# ============================================================================


def create_simple_job_xml(description: str = "") -> str:
    """建立簡單的 job XML 配置"""
    return f"""<?xml version='1.1' encoding='UTF-8'?>
<project>
  <description>{description}</description>
  <keepDependencies>false</keepDependencies>
  <properties/>
  <scm class="hudson.scm.NullSCM"/>
  <canRoam>true</canRoam>
  <disabled>false</disabled>
  <blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
  <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
  <triggers/>
  <concurrentBuild>false</concurrentBuild>
  <builders/>
  <publishers/>
  <buildWrappers/>
</project>"""


# ============================================================================
# 測試函數 - delete-builds 指令
# ============================================================================


def test_delete_builds_single(run_jenkee_authed):
    """
    測試刪除單一 build（使用 --yes-i-really-mean-it flag）

    對應 test plan 步驟 2
    """
    # Arrange: 使用已有 builds 的 test-job-1
    # 先觸發一個 build 確保有資料
    build_result = run_jenkee_authed.run("build", "test-job-1", "-s")
    assert build_result.returncode == 0, "Should trigger build successfully"

    # 取得 build 列表
    list_result = run_jenkee_authed.run("list-builds", "test-job-1")
    assert list_result.returncode == 0
    builds_before = parse_build_list(list_result.stdout)
    assert builds_before.count > 0, "Should have at least one build"

    # 選擇第一個 build 來刪除
    build_to_delete = min(builds_before.build_numbers)

    # Act: 刪除單一 build
    result = run_jenkee_authed.run(
        "delete-builds", "test-job-1", str(build_to_delete), "--yes-i-really-mean-it"
    )

    # Assert: 驗證執行成功
    assert result.returncode == 0, f"delete-builds should succeed, got: {result.stderr}"
    assert "✓" in result.stdout or "success" in result.stdout.lower() or "deleted" in result.stdout.lower(), \
        "Should show success message"

    # Verify: 驗證 build 已刪除
    list_after = run_jenkee_authed.run("list-builds", "test-job-1")
    builds_after = parse_build_list(list_after.stdout)
    assert not builds_after.contains(build_to_delete), \
        f"Build #{build_to_delete} should be deleted"


def test_delete_builds_range(run_jenkee_authed):
    """
    測試刪除 build 範圍（使用 --yes-i-really-mean-it flag）

    對應 test plan 步驟 4
    """
    # Arrange: 先建立多個 builds（使用 test-job-2 避免衝突）
    job_name = "test-job-2"

    # 觸發數個 builds
    for i in range(3):
        build_result = run_jenkee_authed.run("build", job_name, "-s")
        assert build_result.returncode == 0

    # 取得 build 列表
    list_result = run_jenkee_authed.run("list-builds", job_name)
    builds_before = parse_build_list(list_result.stdout)
    assert builds_before.count >= 3, "Should have at least 3 builds"

    # 選擇範圍（前兩個 build）
    build_numbers = sorted(builds_before.build_numbers)
    start_build = build_numbers[0]
    end_build = build_numbers[1]
    build_range = f"{start_build}-{end_build}"

    # Act: 刪除範圍
    result = run_jenkee_authed.run(
        "delete-builds", job_name, build_range, "--yes-i-really-mean-it"
    )

    # Assert: 驗證執行成功
    assert result.returncode == 0, f"delete-builds should succeed, got: {result.stderr}"
    assert "✓" in result.stdout or "success" in result.stdout.lower() or "deleted" in result.stdout.lower(), \
        "Should show success message"

    # Verify: 驗證範圍內的 builds 已刪除
    list_after = run_jenkee_authed.run("list-builds", job_name)
    builds_after = parse_build_list(list_after.stdout)

    assert not builds_after.contains(start_build), \
        f"Build #{start_build} should be deleted"
    assert not builds_after.contains(end_build), \
        f"Build #{end_build} should be deleted"


def test_delete_builds_nonexistent(run_jenkee_authed):
    """
    測試刪除不存在的 build

    對應 test plan 錯誤情境測試
    注意：Jenkins CLI 的 delete-builds 在 build 不存在時仍會返回成功，只是報告刪除了 0 個 builds
    """
    # Arrange: 使用不存在的 build 編號
    nonexistent_build = 99999

    # Act: 嘗試刪除並允許失敗
    result = run_jenkee_authed.build_command(
        "delete-builds", "test-job-1", str(nonexistent_build), "--yes-i-really-mean-it"
    ).allow_failure().run()

    # Assert: Jenkins CLI 在 build 不存在時仍會返回成功（returncode 0）
    # 但輸出會顯示 "Deleted 0 builds"
    assert result.returncode == 0, "Command should succeed (Jenkins CLI behavior)"

    # Verify: 驗證輸出顯示沒有刪除任何 build
    assert "deleted 0 builds" in result.stdout.lower(), \
        f"Should show 0 builds deleted, got: {result.stdout}"


def test_delete_builds_nonexistent_job(run_jenkee_authed):
    """
    測試刪除不存在 job 的 builds

    對應 test plan 錯誤情境測試
    """
    # Arrange: 使用不存在的 job
    nonexistent_job = "non-existent-job"

    # Act: 嘗試刪除並允許失敗
    result = run_jenkee_authed.build_command(
        "delete-builds", nonexistent_job, "1", "--yes-i-really-mean-it"
    ).allow_failure().run()

    # Assert: 驗證失敗
    assert result.returncode != 0, "Should fail when job doesn't exist"

    # Verify: 驗證錯誤訊息
    error_output = (result.stdout + result.stderr).lower()
    assert 'error' in error_output or 'failed' in error_output, \
        f"Should have error message, got: {result.stdout + result.stderr}"


def test_delete_builds_with_confirmation_cancelled(run_jenkee_authed):
    """
    測試取消刪除 build 操作（模擬輸入 n）

    對應文件中的「測試 2: 取消刪除」
    """
    # Arrange: 建立測試用 job 與 build
    job_name = "test-delete-builds-cancel"
    job_xml = create_simple_job_xml("Test job for build deletion cancellation")

    run_jenkee_authed.build_command(
        "delete-job", job_name, "--yes-i-really-mean-it"
    ).allow_failure().run()

    create_result = run_jenkee_authed.build_command(
        "create-job", job_name
    ).with_stdin(job_xml).run()
    assert create_result.returncode == 0, "Should create job successfully"

    build_result = run_jenkee_authed.run("build", job_name, "-s")
    assert build_result.returncode == 0, "Should trigger build successfully"

    list_result = run_jenkee_authed.run("list-builds", job_name)
    builds_before = parse_build_list(list_result.stdout)
    assert builds_before.count >= 1, "Should have at least one build"

    build_to_delete = min(builds_before.build_numbers)

    # Act: 嘗試刪除但取消（模擬輸入 'n'）
    result = run_jenkee_authed.build_command(
        "delete-builds", job_name, str(build_to_delete)
    ).with_stdin("n\n").run()

    # Assert: 驗證返回 0（取消不是錯誤）
    assert result.returncode == 0, f"Should return 0 when cancelled, got: {result.returncode}"
    assert "cancelled" in result.stdout.lower() or "canceled" in result.stdout.lower(), \
        "Should show cancellation message"

    # Verify: build 仍然存在
    list_after = run_jenkee_authed.run("list-builds", job_name)
    builds_after = parse_build_list(list_after.stdout)
    assert builds_after.contains(build_to_delete), \
        f"Build #{build_to_delete} should still exist after cancellation"

    # Cleanup
    cleanup_build = run_jenkee_authed.run(
        "delete-builds", job_name, str(build_to_delete), "--yes-i-really-mean-it"
    )
    assert cleanup_build.returncode == 0
    cleanup_job = run_jenkee_authed.run("delete-job", job_name, "--yes-i-really-mean-it")
    assert cleanup_job.returncode == 0


def test_delete_builds_with_confirmation_confirmed(run_jenkee_authed):
    """
    測試互動式確認後刪除 build（模擬輸入 y）

    對應文件中的「測試 1: 互動式確認」
    """
    # Arrange: 建立測試用 job 與 build
    job_name = "test-delete-builds-confirm"
    job_xml = create_simple_job_xml("Test job for build deletion confirmation")

    run_jenkee_authed.build_command(
        "delete-job", job_name, "--yes-i-really-mean-it"
    ).allow_failure().run()

    create_result = run_jenkee_authed.build_command(
        "create-job", job_name
    ).with_stdin(job_xml).run()
    assert create_result.returncode == 0, "Should create job successfully"

    build_result = run_jenkee_authed.run("build", job_name, "-s")
    assert build_result.returncode == 0, "Should trigger build successfully"

    list_result = run_jenkee_authed.run("list-builds", job_name)
    builds_before = parse_build_list(list_result.stdout)
    assert builds_before.count >= 1, "Should have at least one build"

    build_to_delete = min(builds_before.build_numbers)

    # Act: 刪除並確認（模擬輸入 'y'）
    result = run_jenkee_authed.build_command(
        "delete-builds", job_name, str(build_to_delete)
    ).with_stdin("y\n").run()

    # Assert: 驗證執行成功
    assert result.returncode == 0, f"delete-builds should succeed, got: {result.stderr}"
    assert "✓" in result.stdout or "success" in result.stdout.lower() or "deleted" in result.stdout.lower(), \
        "Should show success message"

    # Verify: build 已刪除
    list_after = run_jenkee_authed.run("list-builds", job_name)
    builds_after = parse_build_list(list_after.stdout)
    assert not builds_after.contains(build_to_delete), \
        f"Build #{build_to_delete} should be deleted"

    # Cleanup
    cleanup_job = run_jenkee_authed.run("delete-job", job_name, "--yes-i-really-mean-it")
    assert cleanup_job.returncode == 0


# ============================================================================
# 測試函數 - delete-job 指令
# ============================================================================


def test_delete_job_single(run_jenkee_authed):
    """
    測試刪除單一 job（使用 --yes-i-really-mean-it flag）

    對應 test plan 步驟 8
    """
    # Arrange: 先建立測試用 job
    job_name = "test-delete-job-single"
    job_xml = create_simple_job_xml("Test job for deletion")

    create_result = run_jenkee_authed.build_command(
        "create-job", job_name
    ).with_stdin(job_xml).allow_failure().run()

    # 如果 job 已存在（前次測試殘留），先刪除
    if create_result.returncode != 0:
        delete_old = run_jenkee_authed.build_command(
            "delete-job", job_name, "--yes-i-really-mean-it"
        ).allow_failure().run()
        # 重新建立
        create_result = run_jenkee_authed.build_command(
            "create-job", job_name
        ).with_stdin(job_xml).run()

    assert create_result.returncode == 0, "Should create job successfully"

    # Act: 刪除 job（使用確認 flag）
    result = run_jenkee_authed.run("delete-job", job_name, "--yes-i-really-mean-it")

    # Assert: 驗證執行成功
    assert result.returncode == 0, f"delete-job should succeed, got: {result.stderr}"
    assert "✓" in result.stdout or "success" in result.stdout.lower() or "deleted" in result.stdout.lower(), \
        "Should show success message"

    # Verify: 驗證 job 已刪除（使用 list-jobs）
    list_result = run_jenkee_authed.run("list-jobs", "--all")
    jobs = parse_job_list(list_result.stdout)
    assert job_name not in jobs, f"Job '{job_name}' should be deleted"


def test_delete_job_verify_with_get_job(run_jenkee_authed):
    """
    測試驗證刪除的 job 無法再被取得

    對應 test plan 步驟 9
    """
    # Arrange: 先建立測試用 job
    job_name = "test-delete-job-verify"
    job_xml = create_simple_job_xml("Test job for deletion verification")

    # 清理可能的舊 job
    cleanup = run_jenkee_authed.build_command(
        "delete-job", job_name, "--yes-i-really-mean-it"
    ).allow_failure().run()

    # 建立新 job
    create_result = run_jenkee_authed.build_command(
        "create-job", job_name
    ).with_stdin(job_xml).run()
    assert create_result.returncode == 0

    # Act: 刪除 job（使用確認 flag）
    delete_result = run_jenkee_authed.run("delete-job", job_name, "--yes-i-really-mean-it")
    assert delete_result.returncode == 0

    # Verify: 嘗試取得已刪除的 job 應該失敗
    get_result = run_jenkee_authed.build_command(
        "get-job", job_name
    ).allow_failure().run()

    assert get_result.returncode != 0, \
        "Should fail to get deleted job"


def test_delete_job_multiple(run_jenkee_authed):
    """
    測試批次刪除多個 jobs

    對應 test plan 步驟 10
    """
    # Arrange: 先建立多個測試用 jobs
    job_names = ["test-delete-multi-1", "test-delete-multi-2"]
    job_xml = create_simple_job_xml("Test job for batch deletion")

    for job_name in job_names:
        # 清理可能的舊 job
        cleanup = run_jenkee_authed.build_command(
            "delete-job", job_name, "--yes-i-really-mean-it"
        ).allow_failure().run()

        # 建立新 job
        create_result = run_jenkee_authed.build_command(
            "create-job", job_name
        ).with_stdin(job_xml).run()
        assert create_result.returncode == 0, f"Should create {job_name}"

    # Act: 批次刪除（使用確認 flag）
    result = run_jenkee_authed.run("delete-job", *job_names, "--yes-i-really-mean-it")

    # Assert: 驗證執行成功
    assert result.returncode == 0, f"delete-job should succeed, got: {result.stderr}"
    assert "✓" in result.stdout or "success" in result.stdout.lower() or "deleted" in result.stdout.lower(), \
        "Should show success message"

    # Verify: 驗證所有 jobs 都已刪除
    list_result = run_jenkee_authed.run("list-jobs", "--all")
    jobs = parse_job_list(list_result.stdout)

    for job_name in job_names:
        assert job_name not in jobs, f"Job '{job_name}' should be deleted"


def test_delete_job_nonexistent(run_jenkee_authed):
    """
    測試刪除不存在的 job

    對應 test plan 錯誤情境測試
    """
    # Arrange: 使用不存在的 job 名稱
    nonexistent_job = "non-existent-job-for-deletion"

    # Act: 嘗試刪除並允許失敗（使用確認 flag）
    result = run_jenkee_authed.build_command(
        "delete-job", nonexistent_job, "--yes-i-really-mean-it"
    ).allow_failure().run()

    # Assert: 驗證失敗
    assert result.returncode != 0, "Should fail when deleting non-existent job"

    # Verify: 驗證錯誤訊息
    error_output = (result.stdout + result.stderr).lower()
    assert 'error' in error_output or 'failed' in error_output, \
        f"Should have error message, got: {result.stdout + result.stderr}"


def test_delete_job_with_confirmation_cancelled(run_jenkee_authed):
    """
    測試取消刪除操作（模擬輸入 n）

    對應文件中的「測試 2: 取消刪除」
    """
    # Arrange: 先建立測試用 job
    job_name = "test-delete-cancel"
    job_xml = create_simple_job_xml("Test job for cancellation")

    # 清理可能的舊 job
    cleanup = run_jenkee_authed.build_command(
        "delete-job", job_name, "--yes-i-really-mean-it"
    ).allow_failure().run()

    # 建立新 job
    create_result = run_jenkee_authed.build_command(
        "create-job", job_name
    ).with_stdin(job_xml).run()
    assert create_result.returncode == 0, "Should create job successfully"

    # Act: 嘗試刪除但取消（模擬輸入 'n'）
    result = run_jenkee_authed.build_command(
        "delete-job", job_name
    ).with_stdin("n\n").run()

    # Assert: 驗證返回 0（取消不是錯誤）
    assert result.returncode == 0, f"Should return 0 when cancelled, got: {result.returncode}"
    assert "cancelled" in result.stdout.lower() or "canceled" in result.stdout.lower(), \
        "Should show cancellation message"

    # Verify: 驗證 job 仍然存在
    list_result = run_jenkee_authed.run("list-jobs", "--all")
    jobs = parse_job_list(list_result.stdout)
    assert job_name in jobs, f"Job '{job_name}' should still exist after cancellation"

    # Cleanup: 清理測試 job
    cleanup_final = run_jenkee_authed.run("delete-job", job_name, "--yes-i-really-mean-it")
    assert cleanup_final.returncode == 0


def test_delete_job_with_confirmation_confirmed(run_jenkee_authed):
    """
    測試互動式確認後刪除（模擬輸入 y）

    對應文件中的「測試 1: 互動式確認」
    """
    # Arrange: 先建立測試用 job
    job_name = "test-delete-confirm"
    job_xml = create_simple_job_xml("Test job for confirmation")

    # 清理可能的舊 job
    cleanup = run_jenkee_authed.build_command(
        "delete-job", job_name, "--yes-i-really-mean-it"
    ).allow_failure().run()

    # 建立新 job
    create_result = run_jenkee_authed.build_command(
        "create-job", job_name
    ).with_stdin(job_xml).run()
    assert create_result.returncode == 0, "Should create job successfully"

    # Act: 刪除並確認（模擬輸入 'y'）
    result = run_jenkee_authed.build_command(
        "delete-job", job_name
    ).with_stdin("y\n").run()

    # Assert: 驗證執行成功
    assert result.returncode == 0, f"delete-job should succeed, got: {result.stderr}"
    assert "✓" in result.stdout or "success" in result.stdout.lower() or "deleted" in result.stdout.lower(), \
        "Should show success message"

    # Verify: 驗證 job 已刪除
    list_result = run_jenkee_authed.run("list-jobs", "--all")
    jobs = parse_job_list(list_result.stdout)
    assert job_name not in jobs, f"Job '{job_name}' should be deleted"


# ============================================================================
# 整合測試 - 完整清理工作流程
# ============================================================================


def test_complete_cleanup_workflow(run_jenkee_authed):
    """
    測試完整的清理工作流程

    工作流程：create job -> trigger builds -> delete builds -> delete job
    對應 test plan 場景 A & B
    """
    # 1. 建立測試 job
    job_name = "test-cleanup-workflow"
    job_xml = create_simple_job_xml("Test job for cleanup workflow")

    # 清理可能的舊 job
    cleanup = run_jenkee_authed.build_command(
        "delete-job", job_name, "--yes-i-really-mean-it"
    ).allow_failure().run()

    create_result = run_jenkee_authed.build_command(
        "create-job", job_name
    ).with_stdin(job_xml).run()
    assert create_result.returncode == 0, "Step 1: Should create job"

    # 2. 觸發數個 builds
    for i in range(3):
        build_result = run_jenkee_authed.run("build", job_name, "-s")
        assert build_result.returncode == 0, f"Step 2: Should trigger build {i+1}"

    # 3. 驗證 builds 已建立
    list_builds_result = run_jenkee_authed.run("list-builds", job_name)
    builds = parse_build_list(list_builds_result.stdout)
    assert builds.count >= 3, "Step 3: Should have at least 3 builds"

    # 4. 刪除部分 builds（保留最後一個）
    build_numbers = sorted(builds.build_numbers)
    if len(build_numbers) > 1:
        # 刪除除了最後一個以外的所有 builds
        builds_to_delete = build_numbers[:-1]
        for build_num in builds_to_delete:
            delete_build_result = run_jenkee_authed.run(
                "delete-builds", job_name, str(build_num), "--yes-i-really-mean-it"
            )
            assert delete_build_result.returncode == 0, \
                f"Step 4: Should delete build #{build_num}"

    # 5. 驗證 builds 已刪除（應該只剩一個）
    list_after_delete_builds = run_jenkee_authed.run("list-builds", job_name)
    builds_after = parse_build_list(list_after_delete_builds.stdout)
    assert builds_after.count >= 1, "Step 5: Should have at least 1 build remaining"

    # 6. 刪除 job（包含剩餘的 builds）
    delete_job_result = run_jenkee_authed.run("delete-job", job_name, "--yes-i-really-mean-it")
    assert delete_job_result.returncode == 0, "Step 6: Should delete job"

    # 7. 驗證 job 已刪除
    list_jobs_result = run_jenkee_authed.run("list-jobs", "--all")
    jobs = parse_job_list(list_jobs_result.stdout)
    assert job_name not in jobs, "Step 7: Job should be deleted"


def test_soft_delete_strategy(run_jenkee_authed):
    """
    測試軟刪除策略（先停用，確認，再刪除）

    對應 test plan 場景 B
    """
    # 1. 建立測試 job
    job_name = "test-soft-delete"
    job_xml = create_simple_job_xml("Test job for soft delete")

    # 清理可能的舊 job
    cleanup = run_jenkee_authed.build_command(
        "delete-job", job_name, "--yes-i-really-mean-it"
    ).allow_failure().run()

    create_result = run_jenkee_authed.build_command(
        "create-job", job_name
    ).with_stdin(job_xml).run()
    assert create_result.returncode == 0, "Step 1: Should create job"

    # 2. 停用 job（軟刪除第一步）
    disable_result = run_jenkee_authed.run(
        "disable-job", job_name, "--yes-i-really-mean-it"
    )
    assert disable_result.returncode == 0, "Step 2: Should disable job"

    # 3. 驗證 job 已停用但仍存在
    list_jobs_result = run_jenkee_authed.run("list-jobs", "--all")
    jobs = parse_job_list(list_jobs_result.stdout)
    assert job_name in jobs, "Step 3: Job should still exist"

    # 使用 job-status 驗證已停用
    status_result = run_jenkee_authed.run("job-status", job_name)
    assert status_result.returncode == 0, "Step 3: Should get job status"
    assert "DISABLED" in status_result.stdout.upper() or \
           "disabled" in status_result.stdout.lower() or \
           "false" in status_result.stdout.lower(), \
        "Step 3: Job should be disabled"

    # 4. 刪除 job（軟刪除最後一步）
    delete_result = run_jenkee_authed.run("delete-job", job_name, "--yes-i-really-mean-it")
    assert delete_result.returncode == 0, "Step 4: Should delete job"

    # 5. 驗證 job 已刪除
    list_jobs_after = run_jenkee_authed.run("list-jobs", "--all")
    jobs_after = parse_job_list(list_jobs_after.stdout)
    assert job_name not in jobs_after, "Step 5: Job should be deleted"
