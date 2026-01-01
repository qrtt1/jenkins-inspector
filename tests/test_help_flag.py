"""
測試 --help 和 -h flag

確保 jenkee --help 和 jenkee -h 能正確顯示幫助訊息
"""
import subprocess
import sys


def test_help_flag_long():
    """測試 --help flag"""
    result = subprocess.run(
        ["jenkee", "--help"],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0, "jenkee --help should exit with 0"
    assert "Jenkins Inspector CLI" in result.stdout, "Should show CLI header"
    assert "Available commands:" in result.stdout, "Should list commands"
    assert "auth" in result.stdout, "Should include auth command"


def test_help_flag_short():
    """測試 -h flag"""
    result = subprocess.run(
        ["jenkee", "-h"],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0, "jenkee -h should exit with 0"
    assert "Jenkins Inspector CLI" in result.stdout, "Should show CLI header"
    assert "Available commands:" in result.stdout, "Should list commands"
    assert "auth" in result.stdout, "Should include auth command"


def test_no_args_shows_help():
    """測試沒有參數時也顯示幫助"""
    result = subprocess.run(
        ["jenkee"],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0, "jenkee (no args) should exit with 0"
    assert "Jenkins Inspector CLI" in result.stdout, "Should show CLI header"
    assert "Available commands:" in result.stdout, "Should list commands"


def test_help_command():
    """測試 help 命令（確保沒有破壞原有功能）"""
    result = subprocess.run(
        ["jenkee", "help"],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0, "jenkee help should exit with 0"
    assert "Jenkins Inspector CLI" in result.stdout, "Should show CLI header"
    assert "Available commands:" in result.stdout, "Should list commands"


def test_help_flag_same_as_help_command():
    """測試 --help 和 help 命令輸出相同"""
    result_flag = subprocess.run(
        ["jenkee", "--help"],
        capture_output=True,
        text=True
    )

    result_cmd = subprocess.run(
        ["jenkee", "help"],
        capture_output=True,
        text=True
    )

    assert result_flag.stdout == result_cmd.stdout, \
        "--help and help command should produce same output"
