"""dev host inventory <host>: a read-only report of everything on a host, rendered to HTML on the laptop.

The collector (scripts/inventory/collect.py) is piped over ssh and prints one JSON document; nothing is
installed on the host. Environment variable VALUES are never collected: only names and lengths.
"""
import datetime as dt
import json
import shutil
import subprocess
from html import escape
from pathlib import Path

from devcli import remote
from devcli.config import load_registry
from devcli.errors import DevError
from devcli.paths import PLATFORM_ROOT

COLLECTOR = PLATFORM_ROOT / "scripts" / "inventory" / "collect.py"
COLLECT_TIMEOUT = 170  # AC1: the whole command must finish in under three minutes
MASK_NOTE = "values are never collected; only names and lengths"

DIFF_KEYS = ("containers", "images", "volumes", "networks", "listening", "user_units",
             "system_running", "ollama_models", "env_files", "cron_lines")


# ------------------------------------------------------------------ helpers
def human_bytes(n) -> str:
    """1536 -> '1.5 KB'; None -> '?'."""
    if n is None:
        return "?"
    try:
        n = float(n)
    except (TypeError, ValueError):
        return "?"
    for unit in ("B", "KB", "MB", "GB", "TB", "PB"):
        if abs(n) < 1024 or unit == "PB":
            return f"{int(n)} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return "?"


def _e(v) -> str:
    """Escape any value for HTML; None becomes an empty string, lists are joined."""
    if v is None:
        return ""
    if isinstance(v, bool):
        return "yes" if v else "no"
    if isinstance(v, (list, tuple)):
        return ", ".join(_e(x) for x in v)
    return escape(str(v))


def _table(headers: list[str], rows: list[list[str]], attrs: str = "") -> str:
    """Rows are already-escaped HTML cell strings."""
    if not rows:
        return "<p class=\"empty\">none</p>"
    head = "".join(f"<th>{escape(h)}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f"<table{(' ' + attrs) if attrs else ''}><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def _ul(items: list) -> str:
    if not items:
        return "<p class=\"empty\">none</p>"
    return "<ul>" + "".join(f"<li>{_e(i)}</li>" for i in items) + "</ul>"


def _env_rows(vars_: list[dict]) -> list[list[str]]:
    """One cell per variable: `DATABASE_URL (len 61)`. Values are never present in the data."""
    return [[f"{_e(v.get('name'))} (len {_e(v.get('len'))})"] for v in vars_]


def _section(sid: str, title: str, body: str) -> str:
    return f"<section id=\"{sid}\"><h2>{escape(title)}</h2>{body}</section>"


# ------------------------------------------------------------------ diff
def _ids(data: dict) -> dict[str, set]:
    d = data.get("docker", {}) or {}
    s = data.get("systemd", {}) or {}
    c = data.get("cron", {}) or {}
    cron_lines: set = set(c.get("user", []) or []) | set(c.get("system_crontab", []) or [])
    for f in c.get("cron_d", []) or []:
        cron_lines |= set(f.get("lines", []) or [])
    return {
        "containers": {x["name"] for x in d.get("containers", []) or []},
        "images": {x["repo_tag"] for x in d.get("images", []) or []},
        "volumes": {x["name"] for x in d.get("volumes", []) or []},
        "networks": {x["name"] for x in d.get("networks", []) or []},
        "listening": {f"{x['addr']}:{x['port']}" for x in data.get("listening", []) or []},
        "user_units": {x["name"] for x in s.get("user_units", []) or []},
        "system_running": {x["name"] for x in s.get("system_running", []) or []},
        "ollama_models": {x["name"] for x in (data.get("ollama", {}) or {}).get("models", []) or []},
        "env_files": {x["path"] for x in data.get("env_files", []) or []},
        "cron_lines": cron_lines,
    }


def diff(previous: dict | None, data: dict) -> dict:
    empty = {k: [] for k in DIFF_KEYS}
    if previous is None:
        return {"first_run": True, "added": dict(empty), "removed": dict(empty), "changed": dict(empty)}
    old, new = _ids(previous), _ids(data)
    added = {k: sorted(new[k] - old[k]) for k in DIFF_KEYS}
    removed = {k: sorted(old[k] - new[k]) for k in DIFF_KEYS}
    changed = {k: [] for k in DIFF_KEYS}

    old_c = {c["name"]: c for c in (previous.get("docker", {}) or {}).get("containers", []) or []}
    for c in (data.get("docker", {}) or {}).get("containers", []) or []:
        o = old_c.get(c["name"])
        if o is None:
            continue
        for field in ("image", "state"):
            if o.get(field) != c.get(field):
                changed["containers"].append({"name": c["name"], "field": field, "old": o.get(field), "new": c.get(field)})
    old_env = {f["path"]: {v["name"] for v in f.get("vars", []) or []} for f in previous.get("env_files", []) or []}
    for f in data.get("env_files", []) or []:
        if f["path"] in old_env:
            names = {v["name"] for v in f.get("vars", []) or []}
            if names != old_env[f["path"]]:
                changed["env_files"].append({"path": f["path"], "added": sorted(names - old_env[f["path"]]),
                                             "removed": sorted(old_env[f["path"]] - names)})
    changed["containers"].sort(key=lambda x: (x["name"], x["field"]))
    changed["env_files"].sort(key=lambda x: x["path"])
    return {"first_run": False, "added": added, "removed": removed, "changed": changed}


def change_text(kind: str, item) -> str:
    """A changed entry as one line: `name: old -> new` for containers, `path: +A -B` for env files."""
    if not isinstance(item, dict):
        return str(item)
    if kind == "containers":
        return f"{item['name']}: {item['old']} -> {item['new']}"
    if kind == "env_files":
        parts = [f"+{n}" for n in item.get("added", [])] + [f"-{n}" for n in item.get("removed", [])]
        return f"{item['path']}: variables " + " ".join(parts)
    return str(item)


# ------------------------------------------------------------------ render
CSS = """
body{font-family:system-ui,sans-serif;margin:1.5rem auto;max-width:1200px;padding:0 1rem;color:#222;line-height:1.4}
h1{font-size:1.5rem;margin-bottom:.2rem}h2{font-size:1.2rem;border-bottom:1px solid #ccc;margin-top:2rem;padding-bottom:.2rem}
h3{font-size:1rem;margin:1rem 0 .3rem}nav a{margin-right:.8rem;font-size:.9rem}
table{border-collapse:collapse;width:100%;font-size:.9rem;margin:.4rem 0}th,td{border:1px solid #ddd;padding:.25rem .5rem;text-align:left;vertical-align:top}
th{background:#f3f3f3}tr.detail td{background:#fafafa}code{font-family:ui-monospace,monospace;font-size:.85em}
.empty{color:#777;font-style:italic}.note{color:#555;font-size:.85rem}.warn{color:#a40000}.dangling{color:#a40000;font-weight:600}
.state-running{color:#0a7a0a}.state-exited,.state-dead{color:#a40000}
details summary{cursor:pointer;font-weight:600}.kv td:first-child{font-weight:600;width:12rem}
.added{color:#0a7a0a}.removed{color:#a40000}.changed{color:#b36b00}
"""

JS = """
document.querySelectorAll('tr.toggle').forEach(function(r){r.addEventListener('click',function(){
var d=r.nextElementSibling;if(d&&d.classList.contains('detail')){d.hidden=!d.hidden;}});});
"""

SECTIONS = [("summary", "Summary"), ("changes", "Changes since last run"), ("containers", "Containers"),
            ("compose", "Compose projects"), ("images", "Images"), ("volumes", "Volumes"), ("networks", "Networks"),
            ("env-files", "Env files"), ("listening", "Listening ports"), ("systemd", "Systemd"), ("cron", "Cron"),
            ("ollama", "Ollama"), ("files", "Files"), ("warnings", "Warnings")]


def _render_summary(data: dict) -> str:
    h = data.get("host", {}) or {}
    mem = h.get("mem", {}) or {}
    gpu = data.get("gpu", {}) or {}
    if gpu.get("available"):
        gpu_line = "; ".join(f"{_e(g.get('name'))} {_e(g.get('mem_used'))}/{_e(g.get('mem_total'))} util {_e(g.get('util'))}"
                             for g in gpu.get("devices", []) or []) or "available, no devices"
    else:
        gpu_line = "not available" + (f" ({_e(gpu.get('error'))})" if gpu.get("error") else "")
    n_warn = len(data.get("warnings", []) or [])
    kv = [
        ("host", _e(h.get("hostname"))), ("os", _e(h.get("os"))), ("kernel", _e(h.get("kernel"))),
        ("uptime", _e(h.get("uptime"))), ("load", _e(h.get("load"))), ("cpu", _e(h.get("cpu_count"))),
        ("memory", f"total {_e(mem.get('total_mb'))} MB, used {_e(mem.get('used_mb'))} MB, available {_e(mem.get('available_mb'))} MB"),
        ("gpu", gpu_line), ("users", _e(h.get("users_logged_in")) or "<span class=\"empty\">none</span>"),
        ("collected_at", _e(data.get("collected_at"))),
        ("warnings", f"<a href=\"#warnings\" class=\"{'warn' if n_warn else ''}\">{n_warn} warnings</a>"),
    ]
    out = "<table class=\"kv\"><tbody>" + "".join(f"<tr><td>{escape(k)}</td><td>{v}</td></tr>" for k, v in kv) + "</tbody></table>"
    out += "<h3>Disks</h3>" + _table(
        ["filesystem", "mount", "size", "used", "avail", "use%"],
        [[_e(d.get("filesystem")), _e(d.get("mount")), _e(d.get("size")), _e(d.get("used")), _e(d.get("avail")), _e(d.get("pct"))]
         for d in data.get("disks", []) or []])
    return out


def _render_changes(d: dict) -> str:
    if d["first_run"]:
        return "<p>first run: nothing to compare against</p>"
    rows = []
    for kind, cls in (("added", "added"), ("removed", "removed"), ("changed", "changed")):
        for k in DIFF_KEYS:
            for item in d[kind].get(k, []):
                rows.append([f"<span class=\"{cls}\">{kind}</span>", escape(k), _e(change_text(k, item))])
    if not rows:
        return "<p>no changes</p>"
    return _table(["change", "kind", "item"], rows)


def _render_containers(docker: dict) -> str:
    rows = []
    for c in docker.get("containers", []) or []:
        state = c.get("state") or ""
        rows.append("<tr class=\"toggle\">" + "".join(f"<td>{x}</td>" for x in [
            f"<code>{_e(c.get('name'))}</code>",
            f"<span class=\"state-{escape(str(state))}\">{_e(state)}</span> {_e(c.get('status'))}",
            _e(c.get("image")), _e(c.get("compose_project")), _e(c.get("ports")), _e(c.get("networks")),
            _e(c.get("restart_count"))]) + "</tr>")
        mounts = _table(["source", "destination", "mode"],
                        [[_e(m.get("source")), _e(m.get("destination")), _e(m.get("mode"))] for m in c.get("mounts", []) or []])
        env = _table(["variable (length)"], _env_rows(c.get("env", []) or []), 'data-masked="true"')
        detail = (f"<p class=\"note\">created {_e(c.get('created'))}; compose file {_e(c.get('compose_file')) or '-'}</p>"
                  f"<h3>Mounts</h3>{mounts}<h3>Environment</h3><p class=\"note\">{MASK_NOTE}</p>{env}")
        rows.append(f"<tr class=\"detail\" hidden><td colspan=\"7\">{detail}</td></tr>")
    if not rows:
        return "<p class=\"empty\">none</p>"
    head = "".join(f"<th>{h}</th>" for h in ["name", "state / status", "image", "compose project", "ports", "networks", "restarts"])
    return ("<p class=\"note\">click a row for mounts and environment variable names</p>"
            f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(rows)}</tbody></table>")


def _render_env_files(files: list) -> str:
    out = f"<p class=\"note\">{MASK_NOTE}</p>"
    if not files:
        return out + "<p class=\"empty\">none</p>"
    for f in files:
        out += f"<h3><code>{_e(f.get('path'))}</code></h3>" + _table(["variable (length)"], _env_rows(f.get("vars", []) or []), 'data-masked="true"')
    return out


def _render_systemd(s: dict) -> str:
    return ("<h3>System units running</h3>" + _table(["unit", "description"], [[_e(u.get("name")), _e(u.get("description"))] for u in s.get("system_running", []) or []])
            + "<h3>System timers</h3>" + _table(["timer", "next", "last"], [[_e(t.get("name")), _e(t.get("next")), _e(t.get("last"))] for t in s.get("system_timers", []) or []])
            + "<h3>User units</h3>" + _table(["unit", "load", "active", "sub", "description"],
                                             [[_e(u.get("name")), _e(u.get("load")), _e(u.get("active")), _e(u.get("sub")), _e(u.get("description"))] for u in s.get("user_units", []) or []])
            + "<h3>User timers</h3>" + _table(["timer", "next", "last"], [[_e(t.get("name")), _e(t.get("next")), _e(t.get("last"))] for t in s.get("user_timers", []) or []]))


CRON_NOTE = "cron command lines are shown verbatim; cron KEY=value assignments are masked"


def _render_cron(c: dict) -> str:
    out = f"<p class=\"note\">{CRON_NOTE}</p>"
    out += "<h3>User crontab</h3>" + _ul(c.get("user", []) or [])
    out += "<h3>System crontab</h3>" + _ul(c.get("system_crontab", []) or [])
    out += "<h3>cron.d</h3>"
    cron_d = c.get("cron_d", []) or []
    if not cron_d:
        out += "<p class=\"empty\">none</p>"
    for f in cron_d:
        out += f"<h4><code>{_e(f.get('file'))}</code></h4>" + _ul(f.get("lines", []) or [])
    out += "<h3>Periodic</h3>"
    per = c.get("periodic", {}) or {}
    out += _table(["period", "entries"], [[escape(p), _e(per.get(p, [])) or "<span class=\"empty\">none</span>"] for p in ("hourly", "daily", "weekly", "monthly")])
    return out


def _render_ollama(o: dict) -> str:
    if not o.get("available"):
        return f"<p class=\"empty\">not available{(': ' + _e(o.get('error'))) if o.get('error') else ''}</p>"
    return ("<h3>Models</h3>" + _table(["name", "id", "size", "modified"], [[_e(m.get("name")), _e(m.get("id")), _e(m.get("size")), _e(m.get("modified"))] for m in o.get("models", []) or []])
            + "<h3>Running</h3>" + _table(["name", "size", "processor", "until"], [[_e(r.get("name")), _e(r.get("size")), _e(r.get("processor")), _e(r.get("until"))] for r in o.get("running", []) or []]))


def _render_files(f: dict) -> str:
    out = ""
    roots = f.get("roots", []) or []
    if not roots:
        out += "<p class=\"empty\">no roots</p>"
    for r in roots:
        out += f"<h3><code>{_e(r.get('path'))}</code> ({escape(human_bytes(r.get('size_bytes')))})</h3>"
        out += _table(["name", "kind", "size", "modified"],
                      [[_e(x.get("name")), _e(x.get("kind")), escape(human_bytes(x.get("size_bytes"))), _e(x.get("modified"))] for x in r.get("entries", []) or []])
    out += "<h3>Largest</h3>" + _table(["path", "size"], [[_e(x.get("path")), escape(human_bytes(x.get("size_bytes")))] for x in f.get("largest", []) or []])
    return out


def render(data: dict, previous: dict | None, host: str) -> str:
    docker = data.get("docker", {}) or {}
    d = diff(previous, data)
    parts = {
        "summary": _render_summary(data),
        "changes": _render_changes(d),
        "containers": f"<p class=\"note\">docker {_e(docker.get('version')) or 'not available'}</p>" + _render_containers(docker),
        "compose": _table(["project", "status", "config files"], [[_e(p.get("name")), _e(p.get("status")), _e(p.get("config_files"))] for p in docker.get("compose", []) or []]),
        "images": _table(["repo:tag", "id", "size", "dangling", "used by"],
                         [[_e(i.get("repo_tag")), f"<code>{_e(i.get('id'))}</code>", _e(i.get("size")),
                           "<span class=\"dangling\">dangling</span>" if i.get("dangling") else "", _e(i.get("used_by"))]
                          for i in docker.get("images", []) or []]),
        "volumes": _table(["name", "driver", "used by"], [[_e(v.get("name")), _e(v.get("driver")), _e(v.get("used_by"))] for v in docker.get("volumes", []) or []]),
        "networks": _table(["name", "driver", "containers"], [[_e(n.get("name")), _e(n.get("driver")), _e(n.get("containers"))] for n in docker.get("networks", []) or []]),
        "env-files": _render_env_files(data.get("env_files", []) or []),
        "listening": _table(["address", "port", "process"], [[_e(p.get("addr")), _e(p.get("port")), _e(p.get("process"))] for p in data.get("listening", []) or []]),
        "systemd": _render_systemd(data.get("systemd", {}) or {}),
        "cron": _render_cron(data.get("cron", {}) or {}),
        "ollama": _render_ollama(data.get("ollama", {}) or {}),
        "files": _render_files(data.get("files", {}) or {}),
        "warnings": _ul(data.get("warnings", []) or []),
    }
    nav = "<nav>" + "".join(f"<a href=\"#{sid}\">{escape(title)}</a>" for sid, title in SECTIONS) + "</nav>"
    body = "".join(_section(sid, title, parts[sid]) for sid, title in SECTIONS)
    return ("<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"utf-8\">"
            f"<title>Inventory: {escape(host)}</title><style>{CSS}</style></head><body>"
            f"<h1>Inventory: {escape(host)}</h1><p class=\"note\">read-only report collected {_e(data.get('collected_at'))}; schema {_e(data.get('schema'))}</p>"
            f"{nav}{body}<script>{JS}</script></body></html>")


# ------------------------------------------------------------------ run
def _collect(alias: str, roots: list[str]) -> dict:
    """Pipe the collector to the host; the file roots are its command-line arguments."""
    if not COLLECTOR.exists():
        raise DevError(f"collector missing: {COLLECTOR}", 2)
    try:
        p = subprocess.run(["ssh", "-o", "BatchMode=yes", alias, "python3", "-", *roots],
                           input=COLLECTOR.read_bytes(), capture_output=True, timeout=COLLECT_TIMEOUT)
    except subprocess.TimeoutExpired:
        raise DevError(f"collector timed out after {COLLECT_TIMEOUT}s on {alias}", 3)
    err = _text(p.stderr).strip()[:300]
    if p.returncode != 0:
        raise DevError(f"collector failed on {alias} (exit {p.returncode}): {err}", p.returncode or 1)
    try:
        return json.loads(_text(p.stdout))
    except ValueError:
        raise DevError(f"collector output is not JSON: {err}", 1)


def _text(v) -> str:
    return v.decode("utf-8", "replace") if isinstance(v, bytes) else (v or "")


def _previous(out_dir: Path) -> dict | None:
    files = sorted(out_dir.glob("*.json"), key=lambda p: (p.stat().st_mtime_ns, p.name))
    if not files:
        return None
    try:
        return json.loads(files[-1].read_text())
    except ValueError:
        return None


def run(host: str, out_dir: Path | None, open_browser: bool) -> Path:
    entry = remote.host_entry(load_registry("environments"), host)
    alias = remote.pick_ssh(entry)
    roots = [entry["deploy_root"]] + list(entry.get("inventory_roots", []) or [])
    data = _collect(alias, roots)

    out_dir = out_dir or Path.home() / "Work" / "inventory" / host
    out_dir.mkdir(parents=True, exist_ok=True)
    previous = _previous(out_dir)
    base = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    stamp, n = base, 1
    while (out_dir / f"{stamp}.json").exists():  # two runs in the same second must not overwrite each other
        n += 1
        stamp = f"{base}-{n}"
    json_path = out_dir / f"{stamp}.json"
    html_path = out_dir / f"{stamp}.html"
    latest = out_dir / "latest.html"

    json_path.write_text(json.dumps(data, indent=1, sort_keys=True))
    html_path.write_text(render(data, previous, host))
    shutil.copyfile(html_path, latest)
    for p in (json_path, html_path, latest):
        print(f"wrote {p}")

    d = diff(previous, data)
    docker = data.get("docker", {}) or {}
    n_added = sum(len(v) for v in d["added"].values())
    n_removed = sum(len(v) for v in d["removed"].values())
    print(f"{host}: {len(docker.get('containers', []) or [])} containers, {len(docker.get('images', []) or [])} images, "
          f"{len(data.get('listening', []) or [])} ports, {len(data.get('warnings', []) or [])} warnings; "
          + ("first run" if d["first_run"] else f"{n_added} added, {n_removed} removed"))

    if open_browser:
        subprocess.Popen(["xdg-open", str(html_path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return html_path
