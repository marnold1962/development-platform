"""CLI-14: exit codes and last-line reason; increment-2 commands refuse cleanly."""
from devcli.main import main


def test_increment_two_commands_refuse(capsys):
    assert main(["list"]) == 2
    assert "increment 2" in capsys.readouterr().err


def test_open_unknown_project_exits_2(capsys):
    assert main(["open", "no-such-project-xyz", "--check"]) == 2
    assert "project not found" in capsys.readouterr().err
