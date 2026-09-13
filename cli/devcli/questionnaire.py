"""The new-project questionnaire (design section 14, CFG-8).

Asks at most the items in questionnaires/new-project.yaml; defaults anything a
registry or the template can answer. Non-interactive when answers are supplied.
"""
import re

import yaml

from devcli.config import load_registry
from devcli.errors import DevError
from devcli.paths import PLATFORM_ROOT

NAME_RE = re.compile(r"^[a-z][a-z0-9-]{1,39}$")


def items() -> list[dict]:
    with (PLATFORM_ROOT / "questionnaires" / "new-project.yaml").open() as f:
        return yaml.safe_load(f)["items"]


def _ask(prompt: str, default):
    shown = f" [{default}]" if default not in (None, "", []) else ""
    raw = input(f"{prompt}{shown}: ").strip()
    if raw == "":
        return default
    return raw


def run(kind: str, target: str, given: dict | None = None, interactive: bool = True) -> dict:
    """Return answers keyed by item key. `given` pre-answers items; missing ones are asked
    (interactive) or defaulted (non-interactive). Raises DevError on an invalid answer."""
    given = dict(given or {})
    hosts = load_registry("environments")["hosts"]
    if target not in hosts:
        raise DevError(f"unknown hosting target '{target}'; registry has: {', '.join(hosts)}", 2)
    answers: dict = {}
    for it in items():
        key = it["key"]
        default = it.get("default")
        if it.get("default_from") == "cli_argument":
            default = kind if kind in it.get("choices", []) else f"{kind}-web"
        elif it.get("default_from") == "registry.environments.hosts":
            default = target
        elif it.get("default_from") == "template":
            default = ["python", "flask", "blueprints", "jinja", "htmx", "postgresql", "alembic", "pytest"]
        if key in given:
            val = given[key]
        elif interactive and default in (None, "", []) and it["kind"] == "text":
            val = _ask(it["prompt"], default)
        elif interactive and it.get("default_from") is None and it["kind"] in ("choice", "list") and key in ("data_sources", "constraints", "branches", "local_db"):
            val = _ask(it["prompt"], default)
        else:
            val = default
        if it["kind"] == "list" and isinstance(val, str):
            val = [v.strip() for v in val.split(",") if v.strip()]
        if it["kind"] == "choice" and "choices" in it and val not in it["choices"]:
            raise DevError(f"questionnaire: '{key}' must be one of {it['choices']}", 2)
        answers[key] = val
    if not answers.get("name") or not NAME_RE.match(str(answers["name"])):
        raise DevError("questionnaire: name must match ^[a-z][a-z0-9-]{1,39}$", 2)
    if not answers.get("purpose"):
        raise DevError("questionnaire: purpose is required", 2)
    if len(answers.get("branches", [])) != 3:
        raise DevError("questionnaire: exactly three branch names (dev, cert, prod)", 2)
    # data_sources given as "name:access" strings become objects
    ds = []
    for d in answers.get("data_sources", []):
        if isinstance(d, dict):
            ds.append(d)
        else:
            n, _, a = str(d).partition(":")
            ds.append({"name": n, "access": a or "read-only"})
    answers["data_sources"] = ds
    return answers
