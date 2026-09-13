"""ADP-1..3, CLI-9, A11: detection, decline writes nothing, adoption on a new branch, then dev open works."""
import subprocess
from pathlib import Path

import pytest

from devcli import adopt, commands, session
from devcli.errors import DevError


def git(d, *a):
    return subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", *a], cwd=d, capture_output=True, text=True, check=True)


@pytest.fixture
def legacy(tmp_path, monkeypatch):
    """A flask repo not created by the platform, living under a fake identity root."""
    root = tmp_path / "as2"; root.mkdir()
    monkeypatch.setattr(adopt, "IDENTITY_ROOTS", {"as2": root, "company": tmp_path / "company"})
    d = root / "old-flask-thing"; d.mkdir()
    (d / "pyproject.toml").write_text('[project]\nname="old"\ndescription="An old Flask app"\ndependencies=["flask","psycopg[binary]","pytest"]\n')
    (d / "app.py").write_text("from flask import Flask, Blueprint\napp = Flask(__name__)\n")
    (d / "README.md").write_text("# Old thing\n")
    (d / "CLAUDE.md").write_text("# Old rules\nKeep it simple.\n")
    git(d, "init", "-q", "-b", "main")
    git(d, "config", "user.email", "t@t"); git(d, "config", "user.name", "t")  # real repos get this from the identity folder
    git(d, "add", "-A"); git(d, "commit", "-q", "-m", "init")
    return d


def test_detect_flask_service(legacy):
    d = adopt.detect(legacy)
    assert d["type"] == "flask-web" and d["kind"] == "service"
    assert "flask" in d["stack"] and "postgresql" in d["stack"] and "pytest" in d["stack"]
    assert d["name"] == "old-flask-thing" and d["purpose"] == "An old Flask app"


def test_decline_writes_nothing(legacy, monkeypatch):
    monkeypatch.setattr("builtins.input", lambda *_: "n")
    with pytest.raises(DevError) as e:
        commands.open_(str(legacy), check_only=True)
    assert "nothing written" in str(e.value)
    assert not (legacy / "project").exists()
    assert git(legacy, "status", "--porcelain").stdout == ""
    assert git(legacy, "branch", "--show-current").stdout.strip() == "main"


def test_adopt_writes_on_new_branch_and_open_works(legacy, monkeypatch, capsys):
    monkeypatch.setattr(session, "verify_platform_installed", lambda: [])
    rc = commands.open_(str(legacy), check_only=True, adopt_flag=True, adopt_answers={"kind": "service"}, interactive=False)
    assert rc == 0
    assert git(legacy, "branch", "--show-current").stdout.strip() == "platform/adopt"
    assert git(legacy, "log", "--oneline", "main").stdout.count("\n") == 1  # main untouched
    assert (legacy / "project" / "profile.yaml").exists() and (legacy / "deploy" / "target.yml").exists()
    cm = (legacy / "CLAUDE.md").read_text()
    assert "rules/platform.md" in cm and "Keep it simple." in cm  # existing content preserved
    assert ".platform/" in (legacy / ".gitignore").read_text()
    out = capsys.readouterr().out
    assert "READY" in out and "old-flask-thing" in out and "DEV: dev -> /platform/dev/old-flask-thing/" in out


def test_adopt_refuses_dirty_tree(legacy):
    (legacy / "junk.txt").write_text("x")
    with pytest.raises(DevError) as e:
        adopt.adopt(legacy, {"kind": "service"}, interactive=False, host="as2")
    assert "dirty" in str(e.value)
    assert not (legacy / "project").exists()


def test_adopt_outside_identity_root_refuses(tmp_path, monkeypatch):
    monkeypatch.setattr(adopt, "IDENTITY_ROOTS", {"as2": tmp_path / "as2", "company": tmp_path / "company"})
    d = tmp_path / "elsewhere"; d.mkdir(); git(d, "init", "-q"); (d / "a.py").write_text("x=1"); git(d, "add", "-A"); git(d, "commit", "-q", "-m", "i")
    with pytest.raises(DevError) as e:
        adopt.adopt(d, {"kind": "desktop"}, interactive=False, host="as2")
    assert "identity folder" in str(e.value)
