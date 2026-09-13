"""CLI-14: exit codes and last-line reason."""
from devcli.main import main


def test_status_outside_a_project_exits_2(capsys, monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    assert main(["status", "--offline"]) == 2
    assert "not inside a platform project" in capsys.readouterr().err


def test_open_unknown_project_exits_2(capsys):
    assert main(["open", "no-such-project-xyz", "--check"]) == 2
    assert "project not found" in capsys.readouterr().err


def test_list_runs(capsys):
    assert main(["list"]) == 0
