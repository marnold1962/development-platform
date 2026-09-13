"""Git and GitHub operations. Deterministic wrappers; no policy here."""
import subprocess
from pathlib import Path

from devcli.errors import DevError


def run(args: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    r = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    if check and r.returncode != 0:
        raise DevError(f"{' '.join(args)} failed: {r.stderr.strip() or r.stdout.strip()}", 1)
    return r


def state(project: Path) -> dict:
    """Branch, dirty count, and whether the folder is a git repo."""
    if not (project / ".git").exists():
        return {"repo": False, "branch": None, "dirty": None}
    branch = run(["git", "branch", "--show-current"], project).stdout.strip() or "(detached)"
    porcelain = run(["git", "status", "--porcelain"], project).stdout.splitlines()
    return {"repo": True, "branch": branch, "dirty": len(porcelain)}


def init_with_branches(project: Path, branches: list[str], message: str) -> None:
    run(["git", "init", "-q", "-b", branches[0]], project)
    run(["git", "add", "-A"], project)
    run(["git", "commit", "-q", "-m", message], project)
    for b in branches[1:]:
        run(["git", "branch", b], project)


def create_github_repo(project: Path, name: str, branches: list[str]) -> str:
    """Create a private repo and push every branch. Returns the URL."""
    r = run(["gh", "repo", "create", name, "--private", "--source", str(project), "--remote", "origin"], project)
    url = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else name
    for b in branches:
        run(["git", "push", "-q", "-u", "origin", b], project)
    return url


def signing_email(path: Path) -> str:
    r = run(["git", "config", "user.email"], path, check=False)
    return r.stdout.strip()
