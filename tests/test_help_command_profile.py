"""測試 help 指令有正確接上 profile 子指令"""
from jenkins_tools.commands.help import HelpCommand


def test_command_list_includes_profile(capsys):
    exit_code = HelpCommand([]).execute()

    assert exit_code == 0
    assert "profile" in capsys.readouterr().out


def test_help_profile_is_not_unknown_command(capsys):
    exit_code = HelpCommand(["profile"]).execute()

    err = capsys.readouterr().err
    assert exit_code == 0
    assert "Unknown command" not in err
