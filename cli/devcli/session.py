"""Readiness summary (design 13A, SES-1..3). The CLI verifies and reports; Claude loads."""
import datetime as dt
from pathlib import Path

from devcli import gitops
from devcli.config import load_registry
from devcli.paths import CLAUDE_HOME, PLATFORM_ROOT, platform_version

REQUIRED_AGENTS = ["code-flask", "database-sql", "documentation", "test", "review", "infrastructure", "deployment"]
REQUIRED_SKILLS = ["platform-flask", "platform-postgresql", "platform-git", "platform-pytest", "platform-documentation", "platform-deployment", "platform-docker", "platform-ssh", "platform-inventory"]
REQUIRED_COMMANDS = ["project-setup", "quick-change", "inspect-database", "review-code", "update-docs", "project-status", "deploy-dev", "deploy-cert", "deploy-prod", "project-reconfigure"]


def verify_platform_installed() -> list[str]:
    """Return missing user-scope files. Empty list means all present."""
    missing = []
    for a in REQUIRED_AGENTS:
        if not (CLAUDE_HOME / "agents" / f"{a}.md").exists():
            missing.append(f"~/.claude/agents/{a}.md")
    for s in REQUIRED_SKILLS + REQUIRED_COMMANDS:
        if not (CLAUDE_HOME / "skills" / s / "SKILL.md").exists():
            missing.append(f"~/.claude/skills/{s}/SKILL.md")
    if not (PLATFORM_ROOT / "rules" / "platform.md").exists():
        missing.append("rules/platform.md")
    return missing


def resolve_data_sources(profile: dict) -> list[tuple[str, str, bool]]:
    dbs = load_registry("databases")["databases"]
    return [(d["name"], d["access"], d["name"] in dbs) for d in profile.get("data_sources", [])]


def build(project: Path, profile: dict, target: dict) -> dict:
    g = gitops.state(project)
    envs = target.get("environments", {})
    configured_branches = [e["branch"] for e in envs.values()]
    installed = platform_version()
    return {
        "project": profile["name"],
        "purpose": profile["purpose"],
        "stack": " / ".join(profile["stack"]),
        "repository": project.name,
        "branch": g["branch"],
        "branch_configured": (g["branch"] in configured_branches) if g["repo"] else None,
        "configured_branches": configured_branches,
        "kind": target["kind"],
        "host": target.get("host"),
        "environments": {k: f"{v['branch']} -> {v['path']}" for k, v in envs.items()},
        "data_sources": resolve_data_sources(profile),
        "platform_installed": installed,
        "platform_expected": profile["platform_version"],
        "missing": verify_platform_installed(),
        "git_repo": g["repo"],
        "dirty": g["dirty"],
        "docs": {
            "specs": (project / "docs" / "specs").is_dir(),
            "decisions": (project / "docs" / "DECISIONS.md").exists(),
            "changes": (project / "docs" / "CHANGES.md").exists(),
        },
        "claude_md": (project / "CLAUDE.md").exists(),
        "time": dt.datetime.now().isoformat(timespec="seconds"),
    }


def render(s: dict) -> str:
    lines = [
        "PROJECT", f"{s['project']} — {s['purpose']}", "",
        "STACK", s["stack"], "",
        "REPOSITORY", s["repository"], "",
        "CURRENT BRANCH",
        (s["branch"] or "(not a git repository)")
        + ("" if s["branch_configured"] in (True, None) else f"   NOT a configured branch; configured: {', '.join(s['configured_branches'])}"),
        "",
        "ENVIRONMENTS",
    ]
    if s["kind"] == "desktop":
        lines.append("desktop: runs on the laptop, never deployed")
    else:
        lines.append(f"host: {s['host']}")
        lines += [f"{k.upper()}: {v}" for k, v in s["environments"].items()]
    lines += ["", "DATA SOURCES"]
    if not s["data_sources"]:
        lines.append("none declared")
    for name, access, ok in s["data_sources"]:
        lines.append(f"{name} ({access})" + ("" if ok else "   UNRESOLVED: not in registries/databases.yaml"))
    lines += ["", "PLATFORM"]
    lines.append(f"installed {s['platform_installed']}, project expects {s['platform_expected']}"
                 + ("" if s["platform_installed"] == s["platform_expected"] else "   VERSION MISMATCH (reported, not fixed)"))
    lines.append("rules loaded" if not s["missing"] else "MISSING: " + ", ".join(s["missing"]))
    lines.append(f"{len(REQUIRED_AGENTS)} specialists available" if not s["missing"] else "specialists incomplete")
    d = s["docs"]
    lines.append("project context: " + ", ".join(k for k, v in d.items() if v) + ("" if all(d.values()) else "   missing: " + ", ".join(k for k, v in d.items() if not v)))
    lines += ["", "GIT"]
    if not s["git_repo"]:
        lines.append("not a git repository")
    else:
        lines.append("clean" if s["dirty"] == 0 else f"dirty ({s['dirty']} changed files)")
    lines += ["", "READY" if not s["missing"] else "NOT READY", f"({s['time']})"]
    return "\n".join(lines)


def write_session_file(project: Path, text: str) -> Path:
    d = project / ".platform"
    d.mkdir(exist_ok=True)
    p = d / "session.md"
    p.write_text("# Readiness summary (written by `dev open`; facts, not instructions)\n\n```\n" + text + "\n```\n")
    return p
