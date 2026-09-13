"""TPL-1, TPL-2, AGT-8, SES-1..3: the template renders, CLAUDE.md is short, the summary is honest."""
import pytest
import subprocess
from pathlib import Path

import yaml

from devcli import scaffold, session
from devcli.config import load_profile, load_target
from devcli.paths import PLATFORM_ROOT

SUBS = {"__PROJECT_NAME__": "demo-app", "__PROJECT_PURPOSE__": "Demo", "__IDENTITY__": "as2",
        "__HOST__": "as2", "__PLATFORM_VERSION__": "0.1.0", "__PLATFORM_PATH__": str(PLATFORM_ROOT)}


def render(tmp_path: Path) -> Path:
    dest = tmp_path / "demo-app"
    scaffold.render("flask", dest, SUBS)
    return dest


def test_template_renders_and_validates(tmp_path):
    dest = render(tmp_path)
    assert load_profile(dest)["name"] == "demo-app"
    t = load_target(dest)
    assert t["environments"]["prod"]["branch"] == "main"
    assert "__PROJECT" not in (dest / "README.md").read_text()


def test_claude_md_under_60_lines_and_imports_rules(tmp_path):
    dest = render(tmp_path)
    text = (dest / "CLAUDE.md").read_text()
    assert len(text.splitlines()) < 60
    assert f"@{PLATFORM_ROOT}/rules/platform.md" in text


def test_template_references_nothing_outside_platform():
    tpl = PLATFORM_ROOT / "templates" / "flask-web"
    for p in tpl.rglob("*"):
        if p.is_file() and p.suffix in {".py", ".md", ".yml", ".yaml", ".toml", ".sh"}:
            txt = p.read_text()
            assert "~/Work/templates" not in txt and "new-project" not in txt, p


def test_readiness_summary_reports_unresolved_and_dirty(tmp_path, monkeypatch):
    dest = render(tmp_path)
    p = yaml.safe_load((dest / "project" / "profile.yaml").read_text())
    p["data_sources"] = [{"name": "not-registered", "access": "read-only"}]
    (dest / "project" / "profile.yaml").write_text(yaml.safe_dump(p))
    subprocess.run(["git", "init", "-q", "-b", "dev"], cwd=dest, check=True)
    monkeypatch.setattr(session, "verify_platform_installed", lambda: [])
    s = session.build(dest, load_profile(dest), load_target(dest))
    text = session.render(s)
    assert "UNRESOLVED" in text
    assert "dirty" in text
    assert "not-registered (read-only)" in text


def test_readiness_summary_not_ready_when_platform_missing(tmp_path, monkeypatch):
    dest = render(tmp_path)
    monkeypatch.setattr(session, "verify_platform_installed", lambda: ["~/.claude/agents/review.md"])
    s = session.build(dest, load_profile(dest), load_target(dest))
    assert "NOT READY" in session.render(s)


def test_template_pyproject_declares_packages_explicitly():
    """A flat layout with app/, deploy/, project/ and migrations/ needs explicit discovery or pip refuses to build."""
    txt = (PLATFORM_ROOT / "templates" / "flask-web" / "pyproject.toml").read_text()
    assert "[build-system]" in txt and 'include = ["app*"]' in txt and 'py-modules = ["config"]' in txt


def test_new_project_purpose_with_colon_and_quotes(tmp_path, monkeypatch):
    """A purpose like 'Run a process: intake "requests"' must not break profile.yaml, target.yml or pyproject."""
    from devcli import commands, gitops
    monkeypatch.setattr(commands, "IDENTITY_ROOTS", {"as2": tmp_path, "company": tmp_path / "c"})
    monkeypatch.setattr(commands.prereq, "check", lambda **k: ["fake"])
    monkeypatch.setattr(gitops, "signing_email", lambda p: "t@t")
    real_run = gitops.run
    monkeypatch.setattr(gitops, "run", lambda args, cwd=None, check=True: real_run(["git", "-c", "user.email=t@t", "-c", "user.name=t", *args[1:]], cwd, check) if args[0] == "git" else real_run(args, cwd, check))
    rc = commands.new("flask", "as2", {"name": "colon-app", "purpose": 'Run a process: intake "requests", plan them'}, interactive=False, github=False, launch=False)
    assert rc == 0
    dest = tmp_path / "colon-app"
    assert load_profile(dest)["purpose"].startswith("Run a process: intake")
    assert (dest / ".git").exists()
    import tomllib
    tomllib.loads((dest / "pyproject.toml").read_text())


def test_failed_new_project_leaves_nothing(tmp_path, monkeypatch):
    from devcli import commands
    monkeypatch.setattr(commands, "IDENTITY_ROOTS", {"as2": tmp_path, "company": tmp_path / "c"})
    monkeypatch.setattr(commands.prereq, "check", lambda **k: ["fake"])
    monkeypatch.setattr(commands.gitops, "init_with_branches", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))
    with pytest.raises(RuntimeError):
        commands.new("flask", "as2", {"name": "boom-app", "purpose": "p"}, interactive=False, github=False, launch=False)
    assert not (tmp_path / "boom-app").exists()
