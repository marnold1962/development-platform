"""Where things are. Nothing here reads the network."""
from pathlib import Path

PLATFORM_ROOT = Path(__file__).resolve().parents[2]  # cli/devcli/paths.py -> platform root
IDENTITY_ROOTS = {"as2": Path.home() / "Work" / "as2", "company": Path.home() / "Work" / "company"}
CLAUDE_HOME = Path.home() / ".claude"
MANIFEST = CLAUDE_HOME / "platform-manifest.txt"  # files installed by `dev platform update`


def platform_version() -> str:
    """The platform version is the latest git tag on the working copy, else 0.0.0."""
    import subprocess

    try:
        out = subprocess.run(
            ["git", "-C", str(PLATFORM_ROOT), "describe", "--tags", "--abbrev=0"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        return out.lstrip("v") or "0.0.0"
    except subprocess.CalledProcessError:
        return "0.0.0"
