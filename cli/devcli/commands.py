"""Subcommand implementations. Each returns 0 or raises DevError."""
import os
import shutil
from pathlib import Path

from devcli import gitops, prereq, questionnaire, scaffold, session
from devcli.config import load_profile, load_target, validate_all_registries
from devcli.errors import DevError
from devcli.paths import CLAUDE_HOME, IDENTITY_ROOTS, MANIFEST, PLATFORM_ROOT, platform_version


# ---------------------------------------------------------------- dev new
def new(kind: str, target: str, answers: dict | None, interactive: bool, github: bool, launch: bool) -> int:
    checked = prereq.check()
    print("prerequisites: " + ", ".join(checked))
    validate_all_registries()
    a = questionnaire.run(kind, target, answers, interactive)
    identity = a.get("identity") or "as2"
    if identity not in IDENTITY_ROOTS:
        raise DevError(f"identity must be one of {list(IDENTITY_ROOTS)}", 2)
    dest = IDENTITY_ROOTS[identity] / a["name"]
    if not IDENTITY_ROOTS[identity].is_dir():
        raise DevError(f"identity folder missing: {IDENTITY_ROOTS[identity]}", 2)
    branches = a["branches"]
    subs = {
        "__PROJECT_NAME__": a["name"],
        "__PROJECT_PURPOSE__": a["purpose"],
        "__IDENTITY__": identity,
        "__HOST__": a["host"],
        "__PLATFORM_VERSION__": platform_version(),
        "__PLATFORM_PATH__": str(PLATFORM_ROOT),
    }
    import yaml
    # Text substitution is safe for Markdown and Python but not for YAML/TOML; the purpose may hold
    # colons or quotes. Substitute an escaped form, then rewrite the YAML files from data.
    subs["__PROJECT_PURPOSE__"] = a["purpose"].replace('"', "'")
    try:
        scaffold.render(kind, dest, subs)
        tpath = dest / "deploy" / "target.yml"
        t = {"kind": "service", "identity": identity, "host": a["host"],
             "environments": {env: {"branch": b, "path": f"/platform/{env}/{a['name']}/"} for env, b in zip(("dev", "cert", "prod"), branches)}}
        tpath.write_text("# Where this project runs. Committed, so it is never guesswork. Validated by registries/schema/target.schema.json.\n" + yaml.safe_dump(t, sort_keys=False))
        ppath = dest / "project" / "profile.yaml"
        p = {"name": a["name"], "purpose": a["purpose"], "type": a["type"], "stack": a["stack"],
             "data_sources": a["data_sources"], "platform_version": platform_version()}
        if a.get("constraints"):
            p["constraints"] = a["constraints"]
        ppath.write_text(yaml.safe_dump(p, sort_keys=False, allow_unicode=True))
        load_profile(dest)
        load_target(dest)
        gitops.init_with_branches(dest, branches, f"Create {a['name']} from the development platform")
    except Exception:
        shutil.rmtree(dest, ignore_errors=True)  # never leave a half-made project behind
        raise
    email = gitops.signing_email(dest)
    if not email:
        raise DevError(f"git identity not resolved in {dest}; refusing (CLI-5)", 2)
    print(f"created {dest} on branches {', '.join(branches)}; commits sign as {email}")
    if github:
        url = gitops.create_github_repo(dest, a["name"], branches)
        print(f"github: {url}")
    else:
        print("github: skipped (--local)")
    for line in _open_impl(dest, launch=False):
        print(line)
    if launch:
        _launch(dest)
    return 0


# ---------------------------------------------------------------- dev open
def _open_impl(project: Path, launch: bool) -> list[str]:
    out: list[str] = []
    if not (project / "project" / "profile.yaml").exists():
        raise DevError(f"{project} has no project/profile.yaml (adopt mode arrives in increment 3)", 2)
    profile = load_profile(project)
    target = load_target(project)
    validate_all_registries()
    missing = session.verify_platform_installed()
    if missing:
        raise DevError("refusing to launch; missing platform files: " + ", ".join(missing) + " (run: dev platform update)", 2)
    if not (project / "CLAUDE.md").exists():
        raise DevError(f"refusing to launch; {project}/CLAUDE.md missing", 2)
    s = session.build(project, profile, target)
    text = session.render(s)
    session.write_session_file(project, text)
    out.append(text)
    return out


def open_(name_or_path: str, check_only: bool, adopt_flag: bool = False, adopt_answers: dict | None = None,
          interactive: bool = True, host: str = "as2") -> int:
    project = _find_project(name_or_path)
    if not (project / "project" / "profile.yaml").exists():
        from devcli import adopt as ad
        if not adopt_flag:
            if not interactive:
                raise DevError(f"{project} has no project/profile.yaml; pass --adopt to bring it under the platform", 2)
            ans = input(f"{project} is not a platform project. Adopt it (write profile.yaml, target.yml, CLAUDE.md on a new branch)? [y/N]: ").strip().lower()
            if ans != "y":
                raise DevError("not adopted; nothing written", 2)
        ad.adopt(project, adopt_answers, interactive, host)
    for line in _open_impl(project, launch=False):
        print(line)
    if not check_only:
        _launch(project)
    return 0


def _find_project(name_or_path: str) -> Path:
    p = Path(name_or_path).expanduser()
    if name_or_path == ".":
        cur = Path.cwd().resolve()
        for cand in (cur, *cur.parents):
            if (cand / "project" / "profile.yaml").exists():
                return cand
        raise DevError("not inside a platform project (no project/profile.yaml in this folder or its parents)", 2)
    if p.is_dir():
        return p.resolve()
    for root in IDENTITY_ROOTS.values():
        cand = root / name_or_path
        if cand.is_dir():
            return cand.resolve()
    raise DevError(f"project not found: {name_or_path} (looked in {', '.join(str(r) for r in IDENTITY_ROOTS.values())})", 2)


def _launch(project: Path) -> None:
    claude = shutil.which("claude")
    if not claude:
        raise DevError("claude not found on PATH", 2)
    os.chdir(project)
    os.execv(claude, ["claude"])


# ---------------------------------------------------------------- dev platform update
def platform_update(pull: bool) -> int:
    if pull:
        gitops.run(["git", "pull", "-q", "--ff-only"], PLATFORM_ROOT)
    installed: list[str] = []
    # remove files from the previous manifest that belong to us
    if MANIFEST.exists():
        for line in MANIFEST.read_text().splitlines():
            p = Path(line)
            if p.exists():
                p.unlink()
            if p.parent.is_dir() and p.parent != CLAUDE_HOME / "agents" and not any(p.parent.iterdir()):
                p.parent.rmdir()
    (CLAUDE_HOME / "agents").mkdir(parents=True, exist_ok=True)
    (CLAUDE_HOME / "skills").mkdir(parents=True, exist_ok=True)
    for src in sorted((PLATFORM_ROOT / "agents").glob("*.md")):
        dst = CLAUDE_HOME / "agents" / src.name
        if dst.exists() and str(dst) not in _previous_manifest():
            raise DevError(f"refusing: {dst} exists and was not installed by the platform (AGT-7)", 2)
        shutil.copy2(src, dst)
        installed.append(str(dst))
    for group in ("skills", "commands"):
        for d in sorted((PLATFORM_ROOT / group).iterdir()):
            if not (d / "SKILL.md").exists():
                continue
            dst = CLAUDE_HOME / "skills" / d.name
            if dst.exists() and str(dst / "SKILL.md") not in _previous_manifest():
                raise DevError(f"refusing: {dst} exists and was not installed by the platform (AGT-7)", 2)
            dst.mkdir(exist_ok=True)
            shutil.copy2(d / "SKILL.md", dst / "SKILL.md")
            installed.append(str(dst / "SKILL.md"))
    hook_dst = CLAUDE_HOME / "hooks" / "platform-gate.sh"
    hook_dst.parent.mkdir(exist_ok=True)
    shutil.copy2(PLATFORM_ROOT / "hooks" / "platform-gate.sh", hook_dst)
    hook_dst.chmod(0o755)
    installed.append(str(hook_dst))
    _register_hook(hook_dst)
    MANIFEST.write_text("\n".join(installed) + "\n")
    print(f"platform {platform_version()} installed: {len(installed)} files at ~/.claude (manifest: {MANIFEST})")
    return 0


def _register_hook(hook_path: Path) -> None:
    """Add the gate as a PreToolUse hook on Bash in ~/.claude/settings.json, once, without touching other hooks."""
    import json
    settings = CLAUDE_HOME / "settings.json"
    data = json.loads(settings.read_text()) if settings.exists() else {}
    hooks = data.setdefault("hooks", {})
    pre = hooks.setdefault("PreToolUse", [])
    command = f"bash '{hook_path}'"
    for entry in pre:
        for h in entry.get("hooks", []):
            if h.get("command") == command:
                return
    pre.append({"matcher": "Bash", "hooks": [{"type": "command", "command": command, "timeout": 20}]})
    settings.write_text(json.dumps(data, indent=2) + "\n")
    print("registered PreToolUse gate hook in ~/.claude/settings.json")


_prev_cache: list[str] | None = None


def _previous_manifest() -> list[str]:
    global _prev_cache
    if _prev_cache is None:
        _prev_cache = MANIFEST.read_text().splitlines() if MANIFEST.exists() else []
    return _prev_cache
