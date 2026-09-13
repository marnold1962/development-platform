"""Render a template into a new project folder. Pure file operations."""
import shutil
from pathlib import Path

from devcli.errors import DevError
from devcli.paths import PLATFORM_ROOT

TEMPLATES = {"flask": "flask-web"}
TEXT_SUFFIXES = {".py", ".md", ".yml", ".yaml", ".toml", ".html", ".css", ".txt", ".example", ".sh", ".cfg", ".ini", ""}


def template_dir(kind: str) -> Path:
    if kind not in TEMPLATES:
        raise DevError(f"unknown project type '{kind}'; increment 1 provides: {', '.join(TEMPLATES)}", 2)
    d = PLATFORM_ROOT / "templates" / TEMPLATES[kind]
    if not d.is_dir():
        raise DevError(f"template missing: {d}", 2)
    return d


def render(kind: str, dest: Path, subs: dict[str, str]) -> list[Path]:
    src = template_dir(kind)
    if dest.exists():
        raise DevError(f"destination exists: {dest}", 2)
    written: list[Path] = []
    for p in sorted(src.rglob("*")):
        rel = p.relative_to(src)
        out = dest / rel
        if p.is_dir():
            out.mkdir(parents=True, exist_ok=True)
            continue
        out.parent.mkdir(parents=True, exist_ok=True)
        if p.suffix in TEXT_SUFFIXES:
            text = p.read_text()
            for k, v in subs.items():
                text = text.replace(k, v)
            out.write_text(text)
            out.chmod(p.stat().st_mode)
        else:
            shutil.copy2(p, out)
        written.append(out)
    return written
