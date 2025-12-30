"""測試 prompt 命令與 prompt override 功能

prompt 命令不需要 Jenkins instance，因此不使用 jenkins_env 相關 fixtures。
改用自訂的 fixture 來管理臨時檔案與環境變數。
"""

import os
import subprocess
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_prompt_file():
    """
    建立臨時 prompt 檔案的 fixture (function scope)

    提供一個臨時檔案路徑，測試結束後自動清理。

    Returns:
        Path: 臨時檔案路徑

    使用範例:
        temp_prompt_file.write_text("custom content")
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as tmp_file:
        tmp_path = Path(tmp_file.name)
        yield tmp_path
        # Cleanup: 測試結束後刪除臨時檔案
        tmp_path.unlink(missing_ok=True)


@pytest.fixture
def run_prompt():
    """
    執行 jenkee prompt 命令的 fixture (function scope)

    提供執行 prompt 命令的函式，支援透過環境變數指定自訂 prompt 檔案。
    不需要 Jenkins instance，因此不使用 jenkins_env。

    Returns:
        function: 執行 prompt 命令的函式

    使用範例:
        # 使用預設 prompt
        result = run_prompt()

        # 使用自訂 prompt 檔案
        result = run_prompt(custom_prompt_file="/path/to/prompt.md")

        # 忽略自訂 prompt
        result = run_prompt(ignore_override=True)
    """
    def _run(custom_prompt_file=None, ignore_override=False):
        env = os.environ.copy()
        if custom_prompt_file:
            env["JENKINS_INSPECTOR_PROMPT_FILE"] = str(custom_prompt_file)

        cmd = ["jenkee", "prompt"]
        if ignore_override:
            cmd.append("--ignore-override")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env
        )
        return result

    return _run


def test_prompt_default_output(run_prompt):
    """測試預設 prompt 輸出包含預期內容"""
    # Arrange: 不設定環境變數，使用內建預設 prompt

    # Act: 執行 prompt 命令
    result = run_prompt()

    # Assert: 驗證預設內容
    assert result.returncode == 0
    assert "Jenkins Inspector (jenkee) - AI Agent Guide" in result.stdout
    assert "關於 jenkee" in result.stdout
    assert "驗證流程" in result.stdout
    assert "常見使用情境" in result.stdout


def test_prompt_override_with_custom_file(temp_prompt_file, run_prompt):
    """測試使用自訂 prompt 檔案覆蓋預設內容"""
    # Arrange: 建立自訂 prompt 內容
    custom_content = """# 我的自訂 Prompt

這是測試用的自訂內容。

## 自訂規則

1. 規則一
2. 規則二
"""
    temp_prompt_file.write_text(custom_content)

    # Act: 執行 prompt 命令
    result = run_prompt(custom_prompt_file=temp_prompt_file)

    # Assert: 驗證使用自訂內容
    assert result.returncode == 0
    assert "我的自訂 Prompt" in result.stdout
    assert "這是測試用的自訂內容" in result.stdout
    assert "自訂規則" in result.stdout

    # Assert: 驗證不包含預設內容
    assert "Jenkins Inspector (jenkee) - AI Agent Guide" not in result.stdout


def test_prompt_error_on_read_failure(run_prompt):
    """測試當自訂檔案讀取失敗時，返回錯誤"""
    # Arrange: 使用臨時目錄而不是檔案（讀取時會失敗）
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Act: 執行 prompt 命令
        result = run_prompt(custom_prompt_file=tmp_dir)

        # Assert: 驗證返回錯誤
        assert result.returncode == 1
        assert "Error reading custom prompt file" in result.stderr


def test_prompt_error_on_empty_custom_file(temp_prompt_file, run_prompt):
    """測試空的自訂 prompt 檔案返回錯誤"""
    # Arrange: 建立空的 prompt 檔案
    temp_prompt_file.write_text("")

    # Act: 執行 prompt 命令
    result = run_prompt(custom_prompt_file=temp_prompt_file)

    # Assert: 驗證返回錯誤
    assert result.returncode == 1
    assert "Error: Custom prompt file is empty" in result.stderr


def test_prompt_error_on_file_not_found(run_prompt):
    """測試自訂 prompt 檔案不存在時返回錯誤"""
    # Arrange: 使用不存在的檔案路徑
    non_existent_file = "/tmp/non-existent-prompt-file-12345.md"

    # Act: 執行 prompt 命令
    result = run_prompt(custom_prompt_file=non_existent_file)

    # Assert: 驗證返回錯誤
    assert result.returncode == 1
    assert "Error: Custom prompt file not found" in result.stderr


def test_prompt_with_env_var_priority(temp_prompt_file, run_prompt):
    """測試環境變數 JENKINS_INSPECTOR_PROMPT_FILE 的優先級"""
    # Arrange: 建立自訂 prompt 檔案
    custom_content = "# 環境變數指定的 Prompt"
    temp_prompt_file.write_text(custom_content)

    # Act: 透過環境變數指定 prompt 檔案
    result = run_prompt(custom_prompt_file=temp_prompt_file)

    # Assert: 驗證使用環境變數指定的檔案
    assert result.returncode == 0
    assert "環境變數指定的 Prompt" in result.stdout


def test_prompt_ignore_override_with_env_var(temp_prompt_file, run_prompt):
    """測試 --ignore-override 忽略環境變數指定的自訂 prompt"""
    # Arrange: 建立自訂 prompt 檔案
    custom_content = "# 自訂 Prompt"
    temp_prompt_file.write_text(custom_content)

    # Act: 使用 --ignore-override flag
    result = run_prompt(custom_prompt_file=temp_prompt_file, ignore_override=True)

    # Assert: 驗證使用預設 prompt，忽略自訂檔案
    assert result.returncode == 0
    assert "Jenkins Inspector (jenkee) - AI Agent Guide" in result.stdout
    assert "自訂 Prompt" not in result.stdout


def test_prompt_ignore_override_without_custom(run_prompt):
    """測試 --ignore-override 在沒有自訂 prompt 時正常運作"""
    # Arrange: 不設定任何自訂 prompt

    # Act: 使用 --ignore-override flag
    result = run_prompt(ignore_override=True)

    # Assert: 驗證使用預設 prompt
    assert result.returncode == 0
    assert "Jenkins Inspector (jenkee) - AI Agent Guide" in result.stdout
