"""Prerequisite checks (CLI-3, CLI-4). Report; never install."""
import platform
import shutil
import subprocess

from devcli.errors import DevError


def _have(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def check(need_docker: bool = False, need_aws: bool = False) -> list[str]:
    if platform.system() != "Linux":
        raise DevError("prerequisite: this platform supports Linux only (Q7)", 2)
    for cmd in ("git", "gh", "claude", "python3"):
        if not _have(cmd):
            raise DevError(f"prerequisite: '{cmd}' not found on PATH", 2)
    r = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True)
    if r.returncode != 0:
        raise DevError("prerequisite: gh is not authenticated (run: gh auth login)", 2)
    if need_docker and not _have("docker"):
        raise DevError("prerequisite: docker not found and the template needs it", 2)
    if need_aws and not _have("aws"):
        raise DevError("prerequisite: aws CLI not found and the target needs it", 2)
    return ["linux", "git", "gh", "gh-auth", "claude", "python3"] + (["docker"] if need_docker else []) + (["aws"] if need_aws else [])
