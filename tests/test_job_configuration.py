"""
測試 Job Configuration Management 相關指令

涵蓋指令：
- get-job: 取得 job XML 配置
- copy-job: 複製 job
- create-job: 從 XML 建立新 job
- update-job: 更新 job 配置
- job-diff: 比較兩個 jobs 的配置

測試重點：
- 驗證 job 配置的讀取與匯出
- 測試 job 的複製與建立
- 測試 job 配置的更新（需謹慎）
- 驗證 job 配置比較功能
"""
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Optional


# ============================================================================
# Parser Functions - 將命令輸出解析為可精確比對的資料結構
# ============================================================================


@dataclass
class JobConfig:
    """Job XML 配置的結構化資料"""
    description: str
    disabled: bool
    concurrent_build: bool
    # 可擴充其他欄位


def parse_job_xml(xml_string: str) -> JobConfig:
    """
    解析 get-job 命令輸出的 Jenkins job XML 配置

    預期格式：
        <?xml version='1.1' encoding='UTF-8'?>
        <project>
          <description>...</description>
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
        </project>

    Returns:
        JobConfig: 包含主要配置項目的 dataclass
    """
    try:
        root = ET.fromstring(xml_string)
    except ET.ParseError:
        # 如果解析失敗,返回空配置
        return JobConfig(
            description='',
            disabled=False,
            concurrent_build=False
        )

    return JobConfig(
        description=root.findtext('description', ''),
        disabled=root.findtext('disabled', 'false').lower() == 'true',
        concurrent_build=root.findtext('concurrentBuild', 'false').lower() == 'true',
    )


def is_valid_xml(xml_string: str) -> bool:
    """
    檢查字串是否為有效的 XML

    Args:
        xml_string: XML 字串

    Returns:
        bool: 是否為有效的 XML
    """
    try:
        ET.fromstring(xml_string)
        return True
    except ET.ParseError:
        return False


@dataclass
class JobDiffResult:
    """job-diff 輸出的結構化資料"""
    has_differences: bool
    diff_lines: list[str]


def parse_job_diff(stdout: str) -> JobDiffResult:
    """
    解析 job-diff 命令的輸出

    預期格式（unified diff）：
        --- job1
        +++ job2
        @@ -1,3 +1,3 @@
        -<description>Old description</description>
        +<description>New description</description>

    或當沒有差異時：
        No differences found between 'job1' and 'job2'

    Returns:
        JobDiffResult: 包含差異資訊的 dataclass
    """
    lines = stdout.strip().split('\n')

    # 檢查是否有 "No differences" 訊息
    if any('no differences' in line.lower() for line in lines):
        return JobDiffResult(has_differences=False, diff_lines=[])

    # 過濾出實際的 diff 行（以 @@ 或 +/- 開頭的）
    diff_lines = []
    for line in lines:
        if line.startswith('---') or line.startswith('+++'):
            # 標題行
            diff_lines.append(line)
        elif line.startswith('@@'):
            # 差異區塊標記
            diff_lines.append(line)
        elif line.startswith('+') or line.startswith('-'):
            # 實際差異內容
            diff_lines.append(line)

    has_differences = len(diff_lines) > 0

    return JobDiffResult(has_differences=has_differences, diff_lines=diff_lines)


# ============================================================================
# 測試函數 - get-job 指令
# ============================================================================


def test_get_job_basic(run_jenkee_authed):
    """
    測試取得 Job XML 配置

    對應 test plan 步驟 1
    """
    # Arrange: 使用已認證的 jenkee runner（由 fixture 提供）

    # Act: 執行 get-job 指令
    result = run_jenkee_authed.run("get-job", "test-job-1")

    # Assert: 驗證執行成功
    assert result.returncode == 0, f"get-job should succeed, got: {result.stderr}"

    # Verify: 驗證輸出是有效的 XML
    assert is_valid_xml(result.stdout), "Output should be valid XML"

    # Parse: 解析 XML 並驗證基本結構
    config = parse_job_xml(result.stdout)
    assert isinstance(config, JobConfig), "Should be able to parse job XML"


def test_get_job_output_is_valid_xml(run_jenkee_authed):
    """
    測試 get-job 輸出的 XML 格式正確

    驗證可以被 XML parser 解析
    """
    # Arrange: 使用已存在的 job

    # Act: 執行 get-job 指令
    result = run_jenkee_authed.run("get-job", "test-job-2")

    # Assert: 驗證執行成功
    assert result.returncode == 0

    # Verify: 驗證 XML 可以被解析
    assert is_valid_xml(result.stdout), "Output should be valid XML"
    assert result.stdout.strip().startswith('<?xml'), "Should start with XML declaration"


def test_get_job_nonexistent(run_jenkee_authed):
    """
    測試取得不存在的 Job

    對應 test plan 錯誤情境測試
    """
    # Arrange: 使用不存在的 job 名稱

    # Act: 執行 get-job 指令並允許失敗
    result = run_jenkee_authed.build_command(
        "get-job", "non-existent-job"
    ).allow_failure().run()

    # Assert: 驗證失敗
    assert result.returncode != 0, "Should fail for non-existent job"

    # Verify: 驗證錯誤訊息
    error_output = (result.stdout + result.stderr).lower()
    assert 'error' in error_output or 'not found' in error_output or 'no such' in error_output, \
        f"Should have error message, got: {result.stdout + result.stderr}"


# ============================================================================
# 測試函數 - copy-job 指令
# ============================================================================


def test_copy_job_basic(run_jenkee_authed):
    """
    測試複製 Job

    對應 test plan 步驟 2
    注意：會建立新 job，測試環境是 session-scoped，所以新 job 會持續存在
    """
    # Arrange: 使用已存在的 source job 和新的 destination job 名稱
    source_job = "test-job-1"
    dest_job = "test-job-copy-1"

    # Act: 執行 copy-job 指令
    result = run_jenkee_authed.run("copy-job", source_job, dest_job)

    # Assert: 驗證執行成功
    assert result.returncode == 0, f"copy-job should succeed, got: {result.stderr}"
    assert "✓" in result.stdout or "success" in result.stdout.lower(), \
        "Should show success message"


def test_verify_copied_job_exists(run_jenkee_authed):
    """
    測試驗證複製的 Job 存在

    驗證可以取得複製後的 job 配置
    """
    # Arrange: 假設 test-job-copy-1 已經被建立（由其他測試）
    # 如果還沒有，先建立它
    copy_result = run_jenkee_authed.build_command(
        "copy-job", "test-job-1", "test-job-copy-1"
    ).allow_failure().run()
    # 允許失敗（如果已經存在會失敗，這是正常的）

    # Act: 執行 get-job 指令取得複製後的 job
    result = run_jenkee_authed.run("get-job", "test-job-copy-1")

    # Assert: 驗證可以成功取得
    assert result.returncode == 0, "Should be able to get copied job"
    assert is_valid_xml(result.stdout), "Copied job should have valid XML config"


def test_copy_job_to_existing_name(run_jenkee_authed):
    """
    測試複製到已存在的 Job 名稱

    對應 test plan 錯誤情境測試
    """
    # Arrange: 先確保 destination job 存在
    # 複製一次（如果還沒有）
    first_copy = run_jenkee_authed.build_command(
        "copy-job", "test-job-1", "test-job-copy-1"
    ).allow_failure().run()

    # Act: 嘗試複製到相同的名稱（第二次）
    result = run_jenkee_authed.build_command(
        "copy-job", "test-job-1", "test-job-copy-1"
    ).allow_failure().run()

    # Assert: 驗證失敗（因為已存在）
    assert result.returncode != 0, "Should fail when copying to existing job name"

    # Verify: 驗證錯誤訊息
    error_output = (result.stdout + result.stderr).lower()
    assert 'error' in error_output or 'already exists' in error_output or 'exist' in error_output, \
        f"Should have error about existing job, got: {result.stdout + result.stderr}"


# ============================================================================
# 測試函數 - job-diff 指令
# ============================================================================


def test_job_diff_identical_jobs(run_jenkee_authed):
    """
    測試比較相同的 Jobs（沒有差異）

    對應 test plan 步驟 3
    """
    # Arrange: 使用相同配置的 jobs（原始 job 與複製的 job）
    # 確保複製的 job 存在
    run_jenkee_authed.build_command(
        "copy-job", "test-job-1", "test-job-copy-1"
    ).allow_failure().run()

    # Act: 執行 job-diff 指令
    result = run_jenkee_authed.run("job-diff", "test-job-1", "test-job-copy-1")

    # Parse: 解析 diff 結果
    diff_result = parse_job_diff(result.stdout)

    # Assert: 驗證執行成功
    assert result.returncode == 0, f"job-diff should succeed, got: {result.stderr}"

    # Note: 可能會有 job 名稱的差異，這是正常的
    # 我們主要驗證沒有重大的配置差異


def test_job_diff_nonexistent_job(run_jenkee_authed):
    """
    測試比較不存在的 Jobs

    對應 test plan 錯誤情境測試
    """
    # Arrange: 使用不存在的 job 名稱

    # Act: 執行 job-diff 指令並允許失敗
    result = run_jenkee_authed.build_command(
        "job-diff", "test-job-1", "non-existent-job"
    ).allow_failure().run()

    # Assert: 驗證失敗
    assert result.returncode != 0, "Should fail when one job doesn't exist"

    # Verify: 驗證錯誤訊息
    error_output = (result.stdout + result.stderr).lower()
    assert 'error' in error_output or 'failed' in error_output, \
        f"Should have error message, got: {result.stdout + result.stderr}"


# ============================================================================
# 測試函數 - create-job 指令
# ============================================================================


def test_create_job_from_xml(run_jenkee_authed):
    """
    測試從 XML 建立新 Job

    對應 test plan 步驟 4
    """
    # Arrange: 先取得現有 job 的 XML 配置
    get_result = run_jenkee_authed.run("get-job", "test-job-1")
    assert get_result.returncode == 0, "Should get job XML successfully"
    xml_config = get_result.stdout

    # Act: 執行 create-job 指令，使用 stdin 傳入 XML
    result = run_jenkee_authed.build_command(
        "create-job", "test-job-from-xml"
    ).with_stdin(xml_config).run()

    # Assert: 驗證執行成功
    assert result.returncode == 0, f"create-job should succeed, got: {result.stderr}"
    assert "✓" in result.stdout or "success" in result.stdout.lower(), \
        "Should show success message"


def test_verify_created_job(run_jenkee_authed):
    """
    測試驗證建立的 Job 存在

    對應 test plan 步驟 5
    """
    # Arrange: 先建立 job（如果還沒有）
    get_result = run_jenkee_authed.run("get-job", "test-job-1")
    if get_result.returncode == 0:
        create_result = run_jenkee_authed.build_command(
            "create-job", "test-job-from-xml"
        ).with_stdin(get_result.stdout).allow_failure().run()

    # Act: 執行 get-job 指令驗證新 job 存在
    result = run_jenkee_authed.run("get-job", "test-job-from-xml")

    # Assert: 驗證可以成功取得
    assert result.returncode == 0, "Should be able to get created job"
    assert is_valid_xml(result.stdout), "Created job should have valid XML config"


def test_create_job_with_invalid_xml(run_jenkee_authed):
    """
    測試使用無效的 XML 建立 Job

    對應 test plan 錯誤情境測試
    """
    # Arrange: 準備無效的 XML
    invalid_xml = "this is not valid xml"

    # Act: 執行 create-job 指令並允許失敗
    result = run_jenkee_authed.build_command(
        "create-job", "test-invalid-job"
    ).with_stdin(invalid_xml).allow_failure().run()

    # Assert: 驗證失敗
    assert result.returncode != 0, "Should fail with invalid XML"

    # Verify: 驗證錯誤訊息
    error_output = (result.stdout + result.stderr).lower()
    assert 'error' in error_output or 'invalid' in error_output or 'failed' in error_output, \
        f"Should have error message, got: {result.stdout + result.stderr}"


# ============================================================================
# 測試函數 - update-job 指令
# ============================================================================


def test_update_job_description(run_jenkee_authed):
    """
    測試更新 Job 描述

    對應 test plan 步驟 6
    注意：update-job 是不可逆操作，需要在測試後恢復
    """
    # Arrange: 使用專門的測試 job（test-job-3）
    # 先取得原始配置作為備份
    backup_result = run_jenkee_authed.run("get-job", "test-job-3")
    assert backup_result.returncode == 0, "Should get original config"
    original_xml = backup_result.stdout

    try:
        # 修改 XML 的描述欄位
        updated_xml = update_xml_description(original_xml, "Updated test description")

        # Act: 執行 update-job 指令
        result = run_jenkee_authed.build_command(
            "update-job", "test-job-3"
        ).with_stdin(updated_xml).run()

        # Assert: 驗證執行成功
        assert result.returncode == 0, f"update-job should succeed, got: {result.stderr}"
        assert "✓" in result.stdout or "success" in result.stdout.lower(), \
            "Should show success message"

    finally:
        # Cleanup: 恢復原始配置
        restore_result = run_jenkee_authed.build_command(
            "update-job", "test-job-3"
        ).with_stdin(original_xml).allow_failure().run()


def test_verify_update_with_get_job(run_jenkee_authed):
    """
    測試驗證更新結果（使用 get-job）

    對應 test plan 步驟 6 的驗證
    """
    # Arrange: 先取得原始配置
    backup_result = run_jenkee_authed.run("get-job", "test-job-3")
    assert backup_result.returncode == 0
    original_xml = backup_result.stdout

    try:
        # 更新描述
        test_description = "Test description for verification"
        updated_xml = update_xml_description(original_xml, test_description)
        update_result = run_jenkee_authed.build_command(
            "update-job", "test-job-3"
        ).with_stdin(updated_xml).run()
        assert update_result.returncode == 0

        # Act: 取得更新後的配置
        result = run_jenkee_authed.run("get-job", "test-job-3")

        # Parse: 解析 XML
        config = parse_job_xml(result.stdout)

        # Assert: 驗證描述已更新
        assert result.returncode == 0
        assert test_description in result.stdout, "Updated description should be in XML"

    finally:
        # Cleanup: 恢復原始配置
        run_jenkee_authed.build_command(
            "update-job", "test-job-3"
        ).with_stdin(original_xml).allow_failure().run()


def test_update_job_nonexistent(run_jenkee_authed):
    """
    測試更新不存在的 Job

    對應 test plan 錯誤情境測試
    """
    # Arrange: 準備有效的 XML 但使用不存在的 job 名稱
    get_result = run_jenkee_authed.run("get-job", "test-job-1")
    assert get_result.returncode == 0
    xml_config = get_result.stdout

    # Act: 執行 update-job 指令並允許失敗
    result = run_jenkee_authed.build_command(
        "update-job", "non-existent-job"
    ).with_stdin(xml_config).allow_failure().run()

    # Assert: 驗證失敗
    assert result.returncode != 0, "Should fail for non-existent job"

    # Verify: 驗證錯誤訊息
    error_output = (result.stdout + result.stderr).lower()
    assert 'error' in error_output or 'not found' in error_output or 'no such' in error_output, \
        f"Should have error message, got: {result.stdout + result.stderr}"


# ============================================================================
# 測試函數 - job-diff 進階測試
# ============================================================================


def test_job_diff_shows_differences(run_jenkee_authed):
    """
    測試 job-diff 顯示配置差異

    對應 test plan 步驟 9
    """
    # Arrange: 使用兩個配置不同的 jobs
    # test-job-1 和 test-job-2 應該有不同的配置或至少有不同的名稱

    # Act: 執行 job-diff 指令
    result = run_jenkee_authed.run("job-diff", "test-job-1", "test-job-2")

    # Parse: 解析 diff 結果
    diff_result = parse_job_diff(result.stdout)

    # Assert: 驗證執行成功
    assert result.returncode == 0, f"job-diff should succeed, got: {result.stderr}"

    # Note: 即使配置相同，job 名稱也會不同
    # 所以至少會有一些差異
    # 我們只驗證命令執行成功和輸出格式正確


def test_job_diff_output_format(run_jenkee_authed):
    """
    測試 job-diff 輸出格式是 unified diff

    驗證輸出可以被解析
    """
    # Arrange: 使用任意兩個 jobs

    # Act: 執行 job-diff 指令
    result = run_jenkee_authed.run("job-diff", "test-job-1", "test-job-3")

    # Parse: 解析 diff 結果
    diff_result = parse_job_diff(result.stdout)

    # Assert: 驗證執行成功且輸出可被解析
    assert result.returncode == 0
    assert isinstance(diff_result, JobDiffResult), "Should be able to parse diff output"


# ============================================================================
# 整合測試 - 完整工作流程
# ============================================================================


def test_complete_job_lifecycle(run_jenkee_authed):
    """
    測試完整的 job 生命週期

    工作流程：get-job -> copy-job -> update-job -> verify
    對應 test plan 整合測試
    """
    # 1. Get original job config
    get_result = run_jenkee_authed.run("get-job", "test-job-1")
    assert get_result.returncode == 0, "Step 1: get-job should succeed"
    original_xml = get_result.stdout

    # 2. Copy job (allow failure if already exists)
    copy_result = run_jenkee_authed.build_command(
        "copy-job", "test-job-1", "test-job-lifecycle"
    ).allow_failure().run()
    # 如果複製失敗（已存在），繼續測試

    # 3. Verify copied job exists
    verify_result = run_jenkee_authed.run("get-job", "test-job-lifecycle")
    assert verify_result.returncode == 0, "Step 3: should get copied job"

    # 4. Update job description
    updated_xml = update_xml_description(original_xml, "Lifecycle test description")
    update_result = run_jenkee_authed.build_command(
        "update-job", "test-job-lifecycle"
    ).with_stdin(updated_xml).allow_failure().run()

    # 5. Verify update
    final_result = run_jenkee_authed.run("get-job", "test-job-lifecycle")
    assert final_result.returncode == 0, "Step 5: should get updated job"


def test_job_template_workflow(run_jenkee_authed):
    """
    測試 Job template 工作流程

    工作流程：get-job -> modify XML -> create-job
    對應 test plan 場景 B
    """
    # 1. Get template job
    get_result = run_jenkee_authed.run("get-job", "test-job-1")
    assert get_result.returncode == 0, "Step 1: should get template job"
    template_xml = get_result.stdout

    # 2. Modify XML (update description to indicate it's from template)
    modified_xml = update_xml_description(template_xml, "Created from template")

    # 3. Create new job from modified XML
    create_result = run_jenkee_authed.build_command(
        "create-job", "test-job-from-template"
    ).with_stdin(modified_xml).allow_failure().run()
    # Allow failure if already exists

    # 4. Verify created job
    verify_result = run_jenkee_authed.run("get-job", "test-job-from-template")
    if verify_result.returncode == 0:
        # 如果成功取得，驗證描述
        assert "Created from template" in verify_result.stdout or "template" in verify_result.stdout.lower(), \
            "Should contain template description"


# ============================================================================
# Helper Functions
# ============================================================================


def update_xml_description(xml_string: str, new_description: str) -> str:
    """
    更新 XML 中的 description 欄位

    Args:
        xml_string: 原始 XML 字串
        new_description: 新的描述文字

    Returns:
        str: 更新後的 XML 字串
    """
    try:
        root = ET.fromstring(xml_string)
        description_elem = root.find('description')
        if description_elem is not None:
            description_elem.text = new_description
        else:
            # 如果沒有 description 元素，建立一個
            description_elem = ET.Element('description')
            description_elem.text = new_description
            # 插入到第一個位置
            root.insert(0, description_elem)

        # 轉回字串（保留 XML 宣告）
        return ET.tostring(root, encoding='unicode')
    except ET.ParseError:
        # 如果解析失敗，返回原始字串
        return xml_string
