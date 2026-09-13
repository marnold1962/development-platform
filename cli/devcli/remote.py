"""SSH transport to a hosting target. Deterministic; no policy."""
import subprocess
from pathlib import Path

from devcli.errors import DevError
from devcli.paths import PLATFORM_ROOT

REMOTE_DIR = PLATFORM_ROOT / "scripts" / "deployment" / "remote"


def host_entry(registry: dict, name: str) -> dict:
    hosts = registry["hosts"]
    if name not in hosts:
        raise DevError(f"host '{name}' is not in registries/environments.yaml", 2)
    return hosts[name]


def pick_ssh(entry: dict) -> str:
    """First reachable ssh alias in the registry's reach list."""
    for r in entry["reach"]:
        alias = r["ssh"]
        p = subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8", alias, "true"], capture_output=True)
        if p.returncode == 0:
            return alias
    raise DevError("host unreachable over: " + ", ".join(r["ssh"] for r in entry["reach"]), 3)


def ssh(alias: str, cmd: str, check: bool = True) -> subprocess.CompletedProcess:
    p = subprocess.run(["ssh", "-o", "BatchMode=yes", alias, cmd], capture_output=True, text=True)
    if check and p.returncode != 0:
        raise DevError(f"remote command failed on {alias}: {(p.stderr or p.stdout).strip()}", p.returncode or 1)
    return p


def install_remote(alias: str, root: str) -> None:
    """Copy the remote script and router config; idempotent, so the host never runs stale logic."""
    ssh(alias, f"mkdir -p {root}/bin {root}/router")
    for name, dest in (("platform-remote.sh", f"{root}/bin/platform-remote.sh"), ("router.conf", f"{root}/router/router.conf")):
        p = subprocess.run(["scp", "-q", str(REMOTE_DIR / name), f"{alias}:{dest}"], capture_output=True, text=True)
        if p.returncode != 0:
            raise DevError(f"scp {name} failed: {p.stderr.strip()}", 1)
    ssh(alias, f"chmod +x {root}/bin/platform-remote.sh")


def remote(alias: str, entry: dict, cmd: str, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    root = entry["deploy_root"]
    port = entry["router_port"]
    argv = " ".join(a for a in args)
    return ssh(alias, f"{root}/bin/platform-remote.sh {root} {port} {cmd} {argv}", check=check)
