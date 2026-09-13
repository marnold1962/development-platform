"""Load and validate configuration and registry files against their schemas (CFG-4, CFG-5)."""
import json
from pathlib import Path

import jsonschema
import yaml

from devcli.errors import DevError
from devcli.paths import PLATFORM_ROOT

SCHEMA_DIR = PLATFORM_ROOT / "registries" / "schema"
REGISTRY_FILES = ["repositories", "environments", "containers", "databases", "tunnels"]


def load_yaml(path: Path) -> dict:
    if not path.exists():
        raise DevError(f"missing file: {path}", 2)
    with path.open() as f:
        data = yaml.safe_load(f)
    if data is None:
        raise DevError(f"empty file: {path}", 2)
    return data


def validate(data: dict, schema_name: str, source: Path) -> None:
    schema = json.loads((SCHEMA_DIR / f"{schema_name}.schema.json").read_text())
    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.path))
    if errors:
        e = errors[0]
        field = "/".join(str(p) for p in e.path) or "(root)"
        raise DevError(f"invalid {source}: field '{field}': {e.message}", 2)


def load_profile(project: Path) -> dict:
    p = project / "project" / "profile.yaml"
    data = load_yaml(p)
    validate(data, "profile", p)
    return data


def load_target(project: Path) -> dict:
    p = project / "deploy" / "target.yml"
    data = load_yaml(p)
    validate(data, "target", p)
    return data


def load_registry(name: str) -> dict:
    p = PLATFORM_ROOT / "registries" / f"{name}.yaml"
    data = load_yaml(p)
    validate(data, name, p)
    return data


def validate_all_registries() -> list[str]:
    """Return the names validated; raise on the first failure."""
    for name in REGISTRY_FILES:
        load_registry(name)
    return REGISTRY_FILES
