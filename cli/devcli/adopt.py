"""Adopt mode (increment 3): bring a repository the platform did not create under it.

ADP-1 detect the stack and prefill; ADP-2 write profile.yaml, target.yml and a minimal
CLAUDE.md on a new branch, never touching the current one; ADP-3 afterwards `dev open` works.
"""
import re
import shutil
from pathlib import Path

import yaml

from devcli import gitops, questionnaire
from devcli.config import load_profile, load_target
from devcli.errors import DevError
from devcli.paths import IDENTITY_ROOTS, PLATFORM_ROOT, platform_version

ADOPT_BRANCH = "platform/adopt"


# ---------------------------------------------------------------- detection
def detect(repo: Path) -> dict:
    """Facts from files present. Returns keys: type, kind, stack, name, purpose, evidence."""
    ev: list[str] = []
    text, raw = "", ""
    for f in ("pyproject.toml", "requirements.txt", "setup.py", "setup.cfg"):
        p = repo / f
        if p.exists():
            raw += p.read_text(errors="ignore") + "\n"; ev.append(f)
    text = raw.lower()
    py_files = list(repo.rglob("*.py"))[:400]
    imports = ""
    for p in py_files:
        try:
            imports += p.read_text(errors="ignore")[:4000].lower()
        except OSError:
            pass
    stack: list[str] = []
    typ, kind = "other", "desktop"
    if py_files or "python" in text:
        stack.append("python")
    if "flask" in text or "from flask" in imports:
        stack += ["flask"]; typ, kind = "flask-web", "service"; ev.append("flask import")
        if "blueprint" in imports: stack.append("blueprints")
        if "jinja" in text or (repo / "templates").exists() or list(repo.rglob("templates")): stack.append("jinja")
        if "htmx" in imports or any("hx-" in (repo / t).read_text(errors="ignore") for t in [] ): stack.append("htmx")
    if "fastapi" in text or "from fastapi" in imports:
        stack += ["fastapi"]; typ, kind = "api", "service"; ev.append("fastapi import")
    if "pyqt6" in text or "from pyqt6" in imports:
        stack += ["pyqt6"]; typ, kind = "python-desktop", "desktop"; ev.append("PyQt6 import")
    if "pyside6" in text or "from pyside6" in imports:
        stack += ["pyside6"]; typ, kind = "python-desktop", "desktop"; ev.append("PySide6 import")
    if (repo / "CMakeLists.txt").exists():
        stack += ["c++", "cmake"]; typ, kind = "cpp-desktop", "desktop"; ev.append("CMakeLists.txt")
        if "qt6" in (repo / "CMakeLists.txt").read_text(errors="ignore").lower(): stack.append("qt6")
    for name, key in (("postgresql", "psycopg"), ("sqlalchemy", "sqlalchemy"), ("alembic", "alembic"), ("pytest", "pytest"), ("sqlserver", "pyodbc"), ("clickhouse", "clickhouse")):
        if key in text or key in imports:
            stack.append(name)
    if (repo / "Dockerfile").exists():
        ev.append("Dockerfile"); kind = "service" if typ in ("flask-web", "api", "other") else kind
    if typ == "other" and stack == []:
        stack = ["unknown"]
    name = re.sub(r"[^a-z0-9-]", "-", repo.name.lower()).strip("-")[:40] or "adopted"
    purpose = ""
    m = re.search(r'description\s*=\s*"([^"]+)"', raw)
    if m:
        purpose = m.group(1)[:300]
    elif (repo / "README.md").exists():
        for line in (repo / "README.md").read_text(errors="ignore").splitlines():
            s = line.strip().lstrip("#").strip()
            if s and not s.startswith("!") and len(s) > 3:
                purpose = s[:300]; break
    return {"type": typ, "kind": kind, "stack": list(dict.fromkeys(stack)), "name": name, "purpose": purpose, "evidence": ev}


# ---------------------------------------------------------------- write
def _identity_for(repo: Path) -> str:
    for ident, root in IDENTITY_ROOTS.items():
        try:
            repo.relative_to(root); return ident
        except ValueError:
            continue
    raise DevError(f"{repo} is not under an identity folder ({', '.join(str(r) for r in IDENTITY_ROOTS.values())}); it cannot be committed", 2)


def adopt(repo: Path, given: dict | None, interactive: bool, host: str) -> Path:
    if (repo / "project" / "profile.yaml").exists():
        raise DevError("already a platform project", 2)
    g = gitops.state(repo)
    if not g["repo"]:
        raise DevError("adopt needs a git repository (run git init first)", 2)
    if g["dirty"]:
        raise DevError(f"working tree is dirty ({g['dirty']} files); adopt only a clean tree", 2)
    identity = _identity_for(repo)
    d = detect(repo)
    print("detected: type=%s kind=%s stack=%s evidence=%s" % (d["type"], d["kind"], ",".join(d["stack"]), ", ".join(d["evidence"]) or "none"))
    pre = {"name": d["name"], "purpose": d["purpose"], "type": d["type"], "stack": d["stack"], "identity": identity}
    pre.update(given or {})
    a = questionnaire.run(d["type"].replace("-web", ""), host, pre, interactive)
    kind = (given or {}).get("kind") or d["kind"]
    if kind not in ("service", "desktop"):
        raise DevError("kind must be service or desktop", 2)
    branch_before = g["branch"]
    gitops.run(["git", "checkout", "-q", "-b", ADOPT_BRANCH], repo)
    try:
        _write_files(repo, a, kind, identity, host)
        load_profile(repo); load_target(repo)
        gitops.run(["git", "add", "-A"], repo)
        gitops.run(["git", "commit", "-q", "-m", f"Adopt {a['name']} into the development platform"], repo)
    except Exception:
        gitops.run(["git", "checkout", "-q", "--", "."], repo, check=False)
        gitops.run(["git", "clean", "-fdq", "--", "project", "deploy", "docs", "CLAUDE.md"], repo, check=False)
        gitops.run(["git", "checkout", "-q", branch_before], repo, check=False)
        gitops.run(["git", "branch", "-D", ADOPT_BRANCH], repo, check=False)
        raise
    print(f"adopted on branch {ADOPT_BRANCH} (from {branch_before}); review and merge when ready")
    return repo


def _write_files(repo: Path, a: dict, kind: str, identity: str, host: str) -> None:
    (repo / "project").mkdir(exist_ok=True)
    profile = {"name": a["name"], "purpose": a["purpose"], "type": a["type"], "stack": a["stack"],
               "data_sources": a["data_sources"], "platform_version": platform_version()}
    if a.get("constraints"):
        profile["constraints"] = a["constraints"]
    (repo / "project" / "profile.yaml").write_text(yaml.safe_dump(profile, sort_keys=False))
    (repo / "deploy").mkdir(exist_ok=True)
    target: dict = {"kind": kind, "identity": identity}
    if kind == "service":
        b = a["branches"]
        target["host"] = host
        target["environments"] = {env: {"branch": br, "path": f"/platform/{env}/{a['name']}/"} for env, br in zip(("dev", "cert", "prod"), b)}
    (repo / "deploy" / "target.yml").write_text("# Written by dev open --adopt. Validated by registries/schema/target.schema.json.\n" + yaml.safe_dump(target, sort_keys=False))
    if kind == "service" and not (repo / "deploy" / "deploy.sh").exists():
        (repo / "deploy" / "deploy.sh").write_text("#!/usr/bin/env bash\nexec dev deploy \"$@\"\n"); (repo / "deploy" / "deploy.sh").chmod(0o755)
    docs = repo / "docs"; (docs / "specs").mkdir(parents=True, exist_ok=True)
    for f, body in (("DECISIONS.md", "# Decisions\n\nAppend-only. `## YYYY-MM-DD — decision` followed by the reason.\n"),
                    ("CHANGES.md", "# Change history\n\nNewest first.\n"),
                    ("specs/README.md", "One spec per feature, with a `status:` line: draft, agreed or built.\n")):
        p = docs / f
        if not p.exists():
            p.write_text(body)
    block = (f"@{PLATFORM_ROOT}/rules/platform.md\n\n## Platform\n\n- Adopted into the development platform. Facts: `project/profile.yaml` (what), `deploy/target.yml` (where), `.platform/session.md` (readiness, written by `dev open`). Print the readiness summary first.\n"
             f"- Specialists: code-flask, database-sql, documentation, test, review, infrastructure, deployment. Commands: /quick-change, /inspect-database, /review-code, /update-docs, /project-status, /deploy-dev, /deploy-cert, /deploy-prod.\n")
    cm = repo / "CLAUDE.md"
    if cm.exists():
        txt = cm.read_text()
        if "rules/platform.md" not in txt:
            cm.write_text(f"# {a['name']}\n\n{block}\n---\n\n" + txt)
    else:
        cm.write_text(f"# {a['name']}\n\n{a['purpose']}\n\n{block}")
    gi = repo / ".gitignore"
    have = gi.read_text() if gi.exists() else ""
    add = [l for l in (".platform/", ".env", ".env.*", "!.env.example", "*.egg-info/") if l not in have.splitlines()]
    if add:
        gi.write_text(have.rstrip("\n") + ("\n" if have else "") + "\n".join(add) + "\n")
