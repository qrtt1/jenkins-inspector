"""測試 help 指令有正確接上 gcp 子指令

gcp 在 cli.py 有 dispatch，但過去 help.py 的 COMMAND_DESCRIPTIONS 沒有列它，
導致 `jenkee help gcp` 回報 Unknown command，也不會出現在 `jenkee help` 的列表裡。
"""
from jenkins_tools.commands.help import HelpCommand


def test_command_list_includes_gcp(capsys):
    exit_code = HelpCommand([]).execute()

    assert exit_code == 0
    assert "gcp" in capsys.readouterr().out


def test_help_gcp_is_not_unknown_command(capsys):
    exit_code = HelpCommand(["gcp"]).execute()

    err = capsys.readouterr().err
    assert exit_code == 0
    assert "Unknown command" not in err
