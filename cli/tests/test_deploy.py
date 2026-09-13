"""DEP-1, DEP-3, DEP-5, DEP-6, CLI-10, TPL-3: preflight refusals, approval binding, list, desktop refusal."""
import json
import subprocess
from pathlib import Path

import pytest
import yaml

from devcli import deploy, scaffold
from devcli.errors import DevError
from devcli.paths import PLATFORM_ROOT

SUBS = {"__PROJECT_NAME__": "demo-app", "__PROJECT_PURPOSE__": "Demo", "__IDENTITY__": "as2",
        "__HOST__": "as2", "__PLATFORM_VERSION__": "0.1.0", "__PLATFORM_PATH__": str(PLATFORM_ROOT)}


def git(dest, *a):
    return subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", *a], cwd=dest, capture_output=True, text=True, check=True)


@pytest.fixture
def project(tmp_path):
    dest = tmp_path / "demo-app"
    scaffold.render("flask", dest, SUBS)
    git(dest, "init", "-q", "-b", "dev")
    git(dest, "add", "-A")
    git(dest, "commit", "-q", "-m", "init")
    git(dest, "branch", "cert"); git(dest, "branch", "main")
    return dest


def test_dirty_tree_refuses(project):
    (project / "x.txt").write_text("x")
    profile = yaml.safe_load((project / "project" / "profile.yaml").read_text())
    target = yaml.safe_load((project / "deploy" / "target.yml").read_text())
    with pytest.raises(DevError) as e:
        deploy._preflight(project, profile, target, "dev", run_tests=False)
    assert "dirty" in str(e.value)


def test_wrong_branch_refuses(project):
    profile = yaml.safe_load((project / "project" / "profile.yaml").read_text())
    target = yaml.safe_load((project / "deploy" / "target.yml").read_text())
    with pytest.raises(DevError) as e:
        deploy._preflight(project, profile, target, "cert", run_tests=False)
    assert "requires branch 'cert'" in str(e.value)


def test_preflight_ok_on_env_branch(project):
    profile = yaml.safe_load((project / "project" / "profile.yaml").read_text())
    target = yaml.safe_load((project / "deploy" / "target.yml").read_text())
    sha = deploy._preflight(project, profile, target, "dev", run_tests=False)
    assert len(sha) == 40


def test_prod_approval_missing_exits_4(project):
    git(project, "checkout", "-q", "main")
    with pytest.raises(DevError) as e:
        deploy.approve(project, "prod", verify_only=True)
    assert e.value.code == 4


def test_prod_approval_lapses_when_head_changes(project):
    git(project, "checkout", "-q", "main")
    sha = deploy._head(project)
    ap = project / ".platform" / "approval-prod.json"; ap.parent.mkdir()
    ap.write_text(json.dumps({"repo": "demo-app", "commit": sha, "branch": "main", "env": "prod", "target": "as2",
                              "by": "t", "time": "now", "backup": "n/a", "rollback": "dev rollback prod", "migrations": []}))
    assert deploy.approve(project, "prod", verify_only=True) == 0
    (project / "y.txt").write_text("y"); git(project, "add", "-A"); git(project, "commit", "-q", "-m", "next")
    with pytest.raises(DevError) as e:
        deploy.approve(project, "prod", verify_only=True)
    assert "does not match HEAD" in str(e.value) and e.value.code == 4


def test_desktop_kind_refuses_deploy(project):
    t = project / "deploy" / "target.yml"
    t.write_text(yaml.safe_dump({"kind": "desktop", "identity": "as2"}))
    with pytest.raises(DevError) as e:
        deploy._project(project)
    assert "only services deploy" in str(e.value)


def test_list_projects_scans_identity_roots(tmp_path, monkeypatch, capsys, project):
    monkeypatch.setattr(deploy, "IDENTITY_ROOTS", {"as2": tmp_path, "company": tmp_path / "nope"})
    (tmp_path / "not-a-project").mkdir()
    deploy.list_projects()
    out = capsys.readouterr().out
    assert "demo-app" in out and "service" in out and "not-a-project" not in out


def test_remote_script_and_router_present_and_valid():
    r = PLATFORM_ROOT / "scripts" / "deployment" / "remote"
    assert (r / "router.conf").exists()
    assert subprocess.run(["bash", "-n", str(r / "platform-remote.sh")]).returncode == 0
