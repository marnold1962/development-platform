"""Host inventory: render(), diff(), human_bytes(), run(). Secrets are never collected or printed."""
import copy
import html
import json
import subprocess
from pathlib import Path

import pytest

from devcli import inventory
from devcli.errors import DevError

FIXTURE = Path(__file__).parent / "fixtures" / "inventory_sample.json"

SECTIONS = ["Summary", "Changes since last run", "Containers", "Compose", "Images", "Volumes", "Networks",
            "Env files", "Listening ports", "Systemd", "Cron", "Ollama", "Files", "Warnings"]

CANARY = "postgresql://user:pass"


@pytest.fixture
def data():
    return json.loads(FIXTURE.read_text())


def esc(s) -> str:
    return html.escape(str(s))


# ---------------------------------------------------------------- render


def test_render_has_every_section_heading(data):
    out = inventory.render(data, None, "as2")
    assert isinstance(out, str)
    for heading in SECTIONS:
        assert heading in out, f"missing section heading: {heading}"


def test_render_lists_every_fixture_item(data):
    out = inventory.render(data, None, "as2")
    for c in data["docker"]["containers"]:
        assert esc(c["name"]) in out
    for i in data["docker"]["images"]:
        assert esc(i["repo_tag"]) in out
    for e in data["env_files"]:
        assert esc(e["path"]) in out
    for l in data["listening"]:
        assert str(l["port"]) in out
    sd = data["systemd"]
    for u in sd["system_running"] + sd["system_timers"] + sd["user_units"] + sd["user_timers"]:
        assert esc(u["name"]) in out
    cron = data["cron"]
    for line in cron["user"] + cron["system_crontab"]:
        assert esc(line) in out
    for f in cron["cron_d"]:
        for line in f["lines"]:
            assert esc(line) in out
    for m in data["ollama"]["models"]:
        assert esc(m["name"]) in out
    for w in data["warnings"]:
        assert esc(w) in out


def test_render_masks_secrets_and_never_prints_values(data):
    # The fixture itself must not contain anything value-looking.
    assert CANARY not in FIXTURE.read_text()

    out = inventory.render(data, None, "as2")
    assert "DATABASE_URL" in out
    assert "len 61" in out
    assert 'data-masked="true"' in out
    assert "never collected" in out
    assert CANARY not in out

    # Negative control: even if the contract is violated upstream and a value leaks
    # into the document, the renderer must not print it.
    poisoned = copy.deepcopy(data)
    poisoned["docker"]["containers"][0]["env"][0]["value"] = "postgresql://user:pass@x/y"
    poisoned["env_files"][0]["vars"][0]["value"] = "postgresql://user:pass@x/y"
    out2 = inventory.render(poisoned, None, "as2")
    assert "postgresql://" not in out2
    assert "user:pass" not in out2


def test_render_escapes_html_in_names(data):
    evil = "<script>alert(1)</script>"
    modified = copy.deepcopy(data)
    modified["docker"]["containers"][0]["name"] = evil
    out = inventory.render(modified, None, "as2")
    assert html.escape(evil) in out
    assert "<script>alert" not in out


def test_render_gpu_error_ollama_models_and_unknown_size(data):
    out = inventory.render(data, None, "as2")
    assert data["gpu"]["available"] is False
    assert esc(data["gpu"]["error"]) in out
    assert "qwen3:14b" in out
    assert "nomic-embed-text:latest" in out
    # A files entry with size_bytes null renders "?" rather than "None" or crashing.
    assert data["files"]["roots"][1]["size_bytes"] is None
    assert "?" in out
    assert "None" not in out.split("Files", 1)[1].split("Warnings", 1)[0]


# ---------------------------------------------------------------- diff


def _buckets(result: dict) -> dict:
    """Normalise diff() output to {key: {"added": [...], "removed": [...], "changed": [...]}}.

    Accepts either {"added": {key: [...]}, ...} or {key: {"added": [...], ...}}.
    """
    kinds = ("added", "removed", "changed")
    out: dict = {}
    if all(k in result for k in kinds) and all(isinstance(result[k], dict) for k in kinds):
        for kind in kinds:
            for key, items in result[kind].items():
                out.setdefault(key, {k: [] for k in kinds})[kind] = list(items)
        return out
    for key, val in result.items():
        if isinstance(val, dict) and any(k in val for k in kinds):
            out[key] = {k: list(val.get(k, [])) for k in kinds}
    return out


def _ids(items, *fields) -> set:
    """Reduce diff entries (strings or dicts) to their identifying value."""
    ids = set()
    for it in items:
        if isinstance(it, dict):
            for f in fields:
                if f in it:
                    ids.add(str(it[f]))
                    break
            else:
                ids.add(json.dumps(it, sort_keys=True))
        else:
            ids.add(str(it))
    return ids


def test_diff_first_run(data):
    result = inventory.diff(None, data)
    assert result["first_run"] is True
    for key, b in _buckets(result).items():
        for kind in ("added", "removed", "changed"):
            assert b[kind] == [], f"{key}.{kind} should be empty on first run"


def test_diff_reports_exact_changes(data):
    prev = data
    cur = copy.deepcopy(data)

    # one container removed
    removed_container = cur["docker"]["containers"].pop(2)["name"]           # old-postgres
    # one container's image changed
    cur["docker"]["containers"][1]["image"] = "ghcr.io/home-assistant/home-assistant:2026.9"
    changed_container = cur["docker"]["containers"][1]["name"]                # ha-bridge
    # one image added
    cur["docker"]["images"].append(
        {"repo_tag": "redis:7", "id": "sha256:0123456789ab", "size": "45MB", "dangling": False, "used_by": []})
    # one env file's var set changed
    cur["env_files"][1]["vars"].append({"name": "HA_URL", "len": 24})
    changed_env = cur["env_files"][1]["path"]                                  # /opt/ha/.env
    # one listening port removed
    removed_port = cur["listening"].pop(3)                                     # 11434, process null

    result = inventory.diff(prev, cur)
    assert result.get("first_run", False) is False
    b = _buckets(result)

    assert _ids(b["containers"]["removed"], "name") == {removed_container}
    assert _ids(b["containers"]["added"], "name") == set()
    assert _ids(b["containers"]["changed"], "name") == {changed_container}

    assert _ids(b["images"]["added"], "repo_tag") == {"redis:7"}
    assert _ids(b["images"]["removed"], "repo_tag") == set()
    assert _ids(b["images"]["changed"], "repo_tag") == set()

    assert _ids(b["env_files"]["changed"], "path") == {changed_env}
    assert _ids(b["env_files"]["added"], "path") == set()
    assert _ids(b["env_files"]["removed"], "path") == set()

    removed_ids = _ids(b["listening"]["removed"], "port")
    assert len(removed_ids) == 1
    assert str(removed_port["port"]) in next(iter(removed_ids))
    assert _ids(b["listening"]["added"], "port") == set()
    assert _ids(b["listening"]["changed"], "port") == set()

    # Nothing else may be non-empty.
    touched = {"containers", "images", "env_files", "listening"}
    for key, kinds in b.items():
        if key in touched:
            continue
        for kind, items in kinds.items():
            assert items == [], f"unexpected diff entries in {key}.{kind}: {items}"


# ---------------------------------------------------------------- human_bytes


def test_human_bytes():
    assert inventory.human_bytes(None) == "?"
    assert inventory.human_bytes(0) == "0 B"
    s = inventory.human_bytes(1536)
    assert "1.5" in s and "K" in s


# ---------------------------------------------------------------- run


REGISTRY = {"hosts": {"as2": {"reach": [{"ssh": "fake"}], "deploy_root": "/x", "router_port": 1,
                              "inventory_roots": ["/y", "/z"]}}}


class _Proc:
    def __init__(self, stdout):
        self.returncode = 0
        self.stdout = stdout
        self.stderr = ""


@pytest.fixture
def fake_remote(monkeypatch, data):
    holder = {"doc": data}

    def fake_run(*a, **kw):
        holder["argv"] = list(a[0]) if a else list(kw.get("args", []))
        return _Proc(json.dumps(holder["doc"]))

    monkeypatch.setattr(inventory, "load_registry", lambda name: REGISTRY)
    monkeypatch.setattr(inventory.remote, "pick_ssh", lambda entry: "fake")
    monkeypatch.setattr(inventory.subprocess, "run", fake_run)
    monkeypatch.setattr(subprocess, "run", fake_run)
    return holder


def test_run_writes_json_html_and_latest_then_diffs(tmp_path, fake_remote, data):
    first = inventory.run("as2", tmp_path, open_browser=False)
    assert isinstance(first, Path)

    second_doc = copy.deepcopy(data)
    second_doc["collected_at"] = "2026-09-13T11:15:00+00:00"
    fake_remote["doc"] = second_doc
    second = inventory.run("as2", tmp_path, open_browser=False)

    jsons = sorted(tmp_path.rglob("*.json"))
    htmls = sorted(p for p in tmp_path.rglob("*.html") if p.name != "latest.html")
    assert len(jsons) == 2, [p.name for p in jsons]
    assert len(htmls) == 2, [p.name for p in htmls]
    assert (tmp_path / "latest.html").exists() or any(p.name == "latest.html" for p in tmp_path.rglob("latest.html"))

    html_out = second.read_text() if second.suffix == ".html" else max(htmls, key=lambda p: p.stat().st_mtime_ns).read_text()
    assert "Changes since last run" in html_out
    assert "first run" not in html_out.lower()
    assert first != second


def test_run_passes_registry_roots_to_collector(tmp_path, fake_remote):
    inventory.run("as2", tmp_path, open_browser=False)
    argv = fake_remote["argv"]
    assert argv[:4] == ["ssh", "-o", "BatchMode=yes", "fake"]
    assert argv[4:] == ["python3", "-", "/x", "/y", "/z"]
    assert inventory.COLLECT_TIMEOUT < 180


def test_render_cron_note_says_assignments_masked(data):
    out = inventory.render(data, None, "as2")
    assert "cron command lines are shown verbatim; cron KEY=value assignments are masked" in out


def test_run_unknown_host_raises(tmp_path, fake_remote):
    with pytest.raises(DevError):
        inventory.run("nope", tmp_path, open_browser=False)
