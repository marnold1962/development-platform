#!/usr/bin/env python3
"""Host-side collector for `dev host inventory`.

Runs on the host via `ssh <alias> python3 - <root>... < collect.py`. Python 3.12,
standard library only. Read-only: it never changes anything on the host.

File roots come from argv[1:]; with none given the user's home is used. Env
files are looked for under each root (depth 1 to 3, never an unbounded walk).

Prints exactly ONE JSON document to stdout. All diagnostics go to stderr.

Secrets never leave the host: for container environment and env files only the
variable NAME and the LENGTH of its value are reported. Never the value, never a
prefix of it. Cron KEY=value assignments are masked the same way; cron command
lines are reported verbatim.
"""

import datetime as _dt
import glob
import json
import os
import re
import shutil
import subprocess
import sys

SCHEMA = 1
DEFAULT_TIMEOUT = 30
DU_TIMEOUT = 60

ENV_FILE_SKIP_SUFFIXES = (".example", ".orig", ".bak")


def resolve_roots(argv):
    """File roots from the command line; the user's home when none are given."""
    roots = [a for a in (argv or []) if a]
    return roots if roots else [os.path.expanduser("~")]


def env_file_globs(roots):
    """Env-file glob patterns derived from the roots.

    Per root: <root>/*/*.env*, <root>/*/.env*, and <root>/**/.env* limited to
    depth 3, expressed as explicit non-recursive patterns (depths 1 to 3)
    rather than an unbounded rglob.
    """
    patterns = []
    for root in roots:
        patterns.append(os.path.join(root, "*", "*.env*"))
        patterns.append(os.path.join(root, "*", ".env*"))
        for depth in (1, 2, 3):
            patterns.append(os.path.join(root, *(["*"] * depth), ".env*"))
    return list(dict.fromkeys(patterns))

WARNINGS: list[str] = []


def warn(msg: str) -> None:
    WARNINGS.append(msg)
    print(f"warning: {msg}", file=sys.stderr)


def run(cmd, timeout=DEFAULT_TIMEOUT, label=None):
    """Run a command; return (rc, stdout, stderr). Never raises.

    rc is None if the binary is missing or the command timed out.
    """
    label = label or " ".join(cmd)
    try:
        p = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            stdin=subprocess.DEVNULL,
            errors="replace",
        )
        return p.returncode, p.stdout, p.stderr
    except FileNotFoundError:
        return None, "", f"{cmd[0]}: not found"
    except subprocess.TimeoutExpired:
        return None, "", f"{label}: timed out after {timeout}s"
    except Exception as e:  # noqa: BLE001
        return None, "", f"{label}: {e!r}"


def run_ok(cmd, timeout=DEFAULT_TIMEOUT, label=None):
    """Run a command and return stdout, or None (with a warning) on failure."""
    label = label or " ".join(cmd)
    rc, out, err = run(cmd, timeout=timeout, label=label)
    if rc != 0:
        first = (err or out).strip().splitlines()
        first = first[0] if first else f"exit {rc}"
        warn(f"{label}: {first}")
        return None
    return out


def read_text(path):
    """Read a text file, or None with a warning."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception as e:  # noqa: BLE001
        warn(f"cannot read {path}: {e.__class__.__name__}: {e}")
        return None


def to_int(s, default=None):
    try:
        return int(s)
    except (TypeError, ValueError):
        return default


def section(name, fn, empty):
    """Run a section collector; on any exception keep the section valid."""
    try:
        return fn()
    except Exception as e:  # noqa: BLE001
        warn(f"section {name} failed: {e.__class__.__name__}: {e}")
        return empty


# --------------------------------------------------------------------------
# host
# --------------------------------------------------------------------------

def collect_host():
    h = {
        "hostname": None,
        "kernel": None,
        "os": None,
        "uptime": None,
        "load": [None, None, None],
        "cpu_count": None,
        "mem": {"total_mb": None, "used_mb": None, "available_mb": None},
        "users_logged_in": [],
    }
    try:
        u = os.uname()
        h["hostname"] = u.nodename
        h["kernel"] = u.release
    except Exception as e:  # noqa: BLE001
        warn(f"uname: {e}")

    txt = read_text("/etc/os-release")
    if txt is not None:
        for line in txt.splitlines():
            if line.startswith("PRETTY_NAME="):
                h["os"] = line.split("=", 1)[1].strip().strip('"')
                break

    out = run_ok(["uptime", "-p"])
    if out is not None:
        h["uptime"] = out.strip()
    else:
        txt = read_text("/proc/uptime")
        if txt:
            secs = int(float(txt.split()[0]))
            h["uptime"] = f"up {secs // 86400}d {(secs % 86400) // 3600}h {(secs % 3600) // 60}m"

    try:
        h["load"] = [round(x, 2) for x in os.getloadavg()]
    except Exception as e:  # noqa: BLE001
        warn(f"getloadavg: {e}")

    h["cpu_count"] = os.cpu_count()

    txt = read_text("/proc/meminfo")
    if txt:
        mi = {}
        for line in txt.splitlines():
            k, _, v = line.partition(":")
            mi[k.strip()] = to_int(v.strip().split()[0]) if v.strip() else None
        total = mi.get("MemTotal")
        avail = mi.get("MemAvailable")
        if total is not None:
            h["mem"]["total_mb"] = total // 1024
        if avail is not None:
            h["mem"]["available_mb"] = avail // 1024
        if total is not None and avail is not None:
            h["mem"]["used_mb"] = (total - avail) // 1024

    rc, out, err = run(["who"])
    if rc == 0:
        users = sorted({ln.split()[0] for ln in out.splitlines() if ln.split()})
        h["users_logged_in"] = users
    else:
        warn(f"who: {(err or out).strip().splitlines()[:1]}")
    return h


HOST_EMPTY = {
    "hostname": None, "kernel": None, "os": None, "uptime": None,
    "load": [None, None, None], "cpu_count": None,
    "mem": {"total_mb": None, "used_mb": None, "available_mb": None},
    "users_logged_in": [],
}


# --------------------------------------------------------------------------
# disks
# --------------------------------------------------------------------------

def collect_disks():
    disks = []
    out = run_ok(["df", "-h", "--output=source,target,size,used,avail,pcent",
                  "-x", "tmpfs", "-x", "devtmpfs", "-x", "squashfs", "-x", "overlay",
                  "-x", "efivarfs", "-x", "fuse.portal", "-x", "fuse.gvfsd-fuse"])
    if out is None:
        return disks
    for line in out.strip().splitlines()[1:]:
        parts = line.split()
        if len(parts) < 6:
            continue
        # Take the fixed numeric columns from the end so a mount point with
        # spaces still parses.
        disks.append({
            "filesystem": parts[0],
            "mount": " ".join(parts[1:-4]),
            "size": parts[-4],
            "used": parts[-3],
            "avail": parts[-2],
            "pct": parts[-1],
        })
    return disks


# --------------------------------------------------------------------------
# gpu
# --------------------------------------------------------------------------

def collect_gpu():
    g = {"available": False, "error": None, "devices": []}
    if shutil.which("nvidia-smi") is None:
        g["error"] = "nvidia-smi: not found"
        return g
    rc, out, err = run([
        "nvidia-smi",
        "--query-gpu=name,memory.used,memory.total,utilization.gpu",
        "--format=csv,noheader",
    ])
    if rc != 0:
        first = (err.strip() or out.strip()).splitlines()
        g["error"] = first[0] if first else f"nvidia-smi exit {rc}"
        return g
    for line in out.strip().splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 4:
            continue
        g["devices"].append({
            "name": parts[0],
            "mem_used": parts[1],
            "mem_total": parts[2],
            "util": parts[3],
        })
    g["available"] = True
    return g


# --------------------------------------------------------------------------
# docker
# --------------------------------------------------------------------------

DOCKER_EMPTY = {
    "version": None,
    "containers": [],
    "images": [],
    "volumes": [],
    "networks": [],
    "compose": [],
}


def docker_json(args, label, timeout=DEFAULT_TIMEOUT):
    """Run `docker <args>` and parse JSON output; returns parsed or None."""
    out = run_ok(["docker"] + args, timeout=timeout, label=label)
    if out is None or not out.strip():
        return None
    try:
        return json.loads(out)
    except json.JSONDecodeError as e:
        warn(f"{label}: bad JSON: {e}")
        return None


def docker_ids(args, label):
    out = run_ok(["docker"] + args, label=label)
    if out is None:
        return []
    return [ln.strip() for ln in out.splitlines() if ln.strip()]


def docker_inspect(kind, ids, label):
    if not ids:
        return []
    args = ["inspect", "--type", kind] if kind else ["inspect"]
    data = docker_json(args + ids, label, timeout=DEFAULT_TIMEOUT * 2)
    return data if isinstance(data, list) else []


def env_name_len(entries):
    """Turn KEY=VALUE strings into [{name, len}] without exposing values."""
    res = []
    for e in entries or []:
        if not isinstance(e, str):
            continue
        name, sep, value = e.partition("=")
        res.append({"name": name, "len": len(value) if sep else 0})
    return res


def collect_docker():
    d = json.loads(json.dumps(DOCKER_EMPTY))
    if shutil.which("docker") is None:
        warn("docker: not found")
        return d

    out = run_ok(["docker", "version", "--format", "{{.Server.Version}}"], label="docker version")
    if out is not None and out.strip():
        d["version"] = out.strip()
    else:
        rc, out2, _ = run(["docker", "--version"])
        if rc == 0:
            d["version"] = out2.strip()

    # containers
    cids = docker_ids(["ps", "-a", "-q", "--no-trunc"], "docker ps -a")
    containers = docker_inspect("container", cids, "docker inspect containers")
    id_to_name = {}
    image_used_by: dict[str, list] = {}
    volume_used_by: dict[str, list] = {}
    for c in containers:
        try:
            name = (c.get("Name") or "").lstrip("/")
            cid = c.get("Id")
            if cid:
                id_to_name[cid] = name
            cfg = c.get("Config") or {}
            state = c.get("State") or {}
            hostcfg = c.get("HostConfig") or {}
            labels = cfg.get("Labels") or {}
            netset = c.get("NetworkSettings") or {}

            ports = []
            for cport, bindings in (netset.get("Ports") or {}).items():
                if bindings:
                    for b in bindings:
                        ports.append(f"{b.get('HostIp', '')}:{b.get('HostPort', '')}->{cport}")
                else:
                    ports.append(cport)

            networks = sorted((netset.get("Networks") or {}).keys())

            mounts = []
            for m in c.get("Mounts") or []:
                src = m.get("Source") or m.get("Name") or ""
                if m.get("Type") == "volume" and m.get("Name"):
                    src = m["Name"]
                    volume_used_by.setdefault(m["Name"], []).append(name)
                mounts.append({
                    "source": src,
                    "destination": m.get("Destination"),
                    "mode": m.get("Mode") or ("rw" if m.get("RW", True) else "ro"),
                })

            img_id = c.get("Image")
            if img_id:
                image_used_by.setdefault(img_id, []).append(name)

            status_text = state.get("Status")
            health = (state.get("Health") or {}).get("Status")
            if health:
                status_text = f"{status_text} ({health})"

            d["containers"].append({
                "name": name,
                "image": cfg.get("Image"),
                "state": state.get("Status"),
                "status": status_text,
                "created": c.get("Created"),
                "restart_count": c.get("RestartCount", 0),
                "ports": ports,
                "networks": networks,
                "mounts": mounts,
                "compose_project": labels.get("com.docker.compose.project"),
                "compose_file": labels.get("com.docker.compose.project.config_files"),
                "env": env_name_len(cfg.get("Env")),
            })
        except Exception as e:  # noqa: BLE001
            warn(f"container parse failed: {e.__class__.__name__}: {e}")

    # images
    iids = docker_ids(["images", "-a", "-q", "--no-trunc"], "docker images")
    iids = list(dict.fromkeys(iids))
    images = docker_inspect("image", iids, "docker inspect images")
    for im in images:
        try:
            iid = im.get("Id") or ""
            tags = im.get("RepoTags") or []
            used = sorted(set(image_used_by.get(iid, [])))
            short = iid.split(":", 1)[-1][:12]
            if tags:
                for t in tags:
                    d["images"].append({
                        "repo_tag": t,
                        "id": short,
                        "size": im.get("Size"),
                        "dangling": False,
                        "used_by": used,
                    })
            else:
                d["images"].append({
                    "repo_tag": "<none>:<none>",
                    "id": short,
                    "size": im.get("Size"),
                    "dangling": True,
                    "used_by": used,
                })
        except Exception as e:  # noqa: BLE001
            warn(f"image parse failed: {e.__class__.__name__}: {e}")

    # volumes
    vnames = docker_ids(["volume", "ls", "-q"], "docker volume ls")
    volumes = docker_inspect("volume", vnames, "docker inspect volumes")
    for v in volumes:
        try:
            d["volumes"].append({
                "name": v.get("Name"),
                "driver": v.get("Driver"),
                "used_by": sorted(set(volume_used_by.get(v.get("Name"), []))),
            })
        except Exception as e:  # noqa: BLE001
            warn(f"volume parse failed: {e.__class__.__name__}: {e}")

    # networks
    nids = docker_ids(["network", "ls", "-q", "--no-trunc"], "docker network ls")
    networks = docker_inspect("network", nids, "docker inspect networks")
    for n in networks:
        try:
            members = []
            for cid, info in (n.get("Containers") or {}).items():
                members.append(id_to_name.get(cid) or (info or {}).get("Name") or cid[:12])
            d["networks"].append({
                "name": n.get("Name"),
                "driver": n.get("Driver"),
                "containers": sorted(members),
            })
        except Exception as e:  # noqa: BLE001
            warn(f"network parse failed: {e.__class__.__name__}: {e}")

    # compose
    data = docker_json(["compose", "ls", "-a", "--format", "json"], "docker compose ls")
    if isinstance(data, list):
        for p in data:
            try:
                cf = p.get("ConfigFiles") or ""
                d["compose"].append({
                    "name": p.get("Name"),
                    "status": p.get("Status"),
                    "config_files": [x for x in cf.split(",") if x] if isinstance(cf, str) else list(cf),
                })
            except Exception as e:  # noqa: BLE001
                warn(f"compose parse failed: {e.__class__.__name__}: {e}")
    return d


# --------------------------------------------------------------------------
# env files
# --------------------------------------------------------------------------

def parse_env_file(text):
    """Return [{name, len}] for KEY=VALUE lines. Values are never retained."""
    vars_ = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].lstrip()
        if "=" not in line:
            continue
        name, _, value = line.partition("=")
        name = name.strip()
        if not re.match(r"^[A-Za-z_][A-Za-z0-9_.\-]*$", name):
            continue
        value = value.strip()
        # Strip one layer of matching quotes so len reflects the value.
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        vars_.append({"name": name, "len": len(value)})
    return vars_


def collect_env_files(patterns):
    res = []
    seen = set()
    for pattern in patterns:
        for path in sorted(glob.glob(pattern, recursive=False)):
            if path in seen:
                continue
            seen.add(path)
            if path.endswith(ENV_FILE_SKIP_SUFFIXES) or not os.path.isfile(path):
                continue
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    text = f.read()
            except Exception as e:  # noqa: BLE001
                warn(f"env file unreadable: {path}: {e.__class__.__name__}: {e}")
                continue
            res.append({"path": path, "vars": parse_env_file(text)})
    return res


# --------------------------------------------------------------------------
# listening
# --------------------------------------------------------------------------

def collect_listening():
    res = []
    out = run_ok(["ss", "-ltnp", "-H"])
    if out is None:
        out = run_ok(["ss", "-ltnp"])
        if out is None:
            return res
        out = "\n".join(out.splitlines()[1:])
    for line in out.splitlines():
        parts = line.split()
        if len(parts) < 4:
            continue
        # ss -H columns: State Recv-Q Send-Q Local Peer [Process]
        local = parts[3]
        if ":" not in local:
            continue
        addr, _, port = local.rpartition(":")
        proc = None
        if "users:((" in line:
            names = re.findall(r'\("([^"]+)",pid=(\d+)', line)
            if names:
                proc = ",".join(f"{n}[{p}]" for n, p in dict.fromkeys(names))
        res.append({"addr": addr, "port": to_int(port, port), "process": proc})
    res.sort(key=lambda r: (r["port"] if isinstance(r["port"], int) else 0, r["addr"]))
    if res and all(r["process"] is None for r in res):
        warn("ss -ltnp: no process names; without sudo ss only shows processes for the user's own sockets")
    return res


# --------------------------------------------------------------------------
# systemd
# --------------------------------------------------------------------------

SYSTEMD_EMPTY = {
    "system_running": [],
    "system_timers": [],
    "user_units": [],
    "user_timers": [],
}


def parse_units(out, fields=5):
    """UNIT LOAD ACTIVE SUB DESCRIPTION... -> dicts."""
    res = []
    for line in out.splitlines():
        parts = line.split(None, fields - 1)
        if len(parts) < 4:
            continue
        while len(parts) < fields:
            parts.append("")
        res.append({
            "name": parts[0],
            "load": parts[1],
            "active": parts[2],
            "sub": parts[3],
            "description": parts[4].strip(),
        })
    return res


_TS = r"(?:-|n/a|\w{3} \d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?: \S+)?)"
TIMER_RE = re.compile(
    r"^(?P<next>" + _TS + r")\s+(?P<left>\S.*?)\s+(?P<last>" + _TS + r")\s+(?P<passed>\S.*?)\s+"
    r"(?P<unit>\S+\.timer)(?:\s+(?P<activates>\S+))?\s*$"
)


def parse_timers(out):
    """Parse `systemctl list-timers --plain --no-legend`.

    Columns: NEXT LEFT LAST PASSED UNIT ACTIVATES. NEXT/LAST are timestamps
    like "Sun 2026-09-13 12:00:00 UTC" or "-"; LEFT/PASSED are free text.
    """
    res = []
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        m = TIMER_RE.match(line)
        if not m:
            toks = line.split()
            unit = next((t for t in toks if t.endswith(".timer")), None)
            if unit is None:
                continue
            warn(f"list-timers: unparsed line for {unit}")
            res.append({"name": unit, "next": None, "last": None})
            continue
        nxt = m.group("next")
        last = m.group("last")
        res.append({
            "name": m.group("unit"),
            "next": None if nxt in ("-", "n/a") else nxt,
            "last": None if last in ("-", "n/a") else last,
        })
    return res


def collect_systemd():
    s = json.loads(json.dumps(SYSTEMD_EMPTY))
    if shutil.which("systemctl") is None:
        warn("systemctl: not found")
        return s
    out = run_ok(["systemctl", "list-units", "--type=service", "--state=running",
                  "--no-pager", "--no-legend", "--plain"], label="systemctl list-units")
    if out is not None:
        s["system_running"] = [{"name": u["name"], "description": u["description"]}
                               for u in parse_units(out)]
    out = run_ok(["systemctl", "list-timers", "--all", "--no-pager", "--no-legend", "--plain"],
                 label="systemctl list-timers")
    if out is not None:
        s["system_timers"] = parse_timers(out)
    out = run_ok(["systemctl", "--user", "list-units", "--type=service,timer", "--all",
                  "--no-pager", "--no-legend", "--plain"], label="systemctl --user list-units")
    if out is not None:
        s["user_units"] = parse_units(out)
    out = run_ok(["systemctl", "--user", "list-timers", "--all", "--no-pager", "--no-legend",
                  "--plain"], label="systemctl --user list-timers")
    if out is not None:
        s["user_timers"] = parse_timers(out)
    return s


# --------------------------------------------------------------------------
# cron
# --------------------------------------------------------------------------

CRON_EMPTY = {
    "user": [],
    "system_crontab": [],
    "cron_d": [],
    "periodic": {"hourly": [], "daily": [], "weekly": [], "monthly": []},
}


# A cron environment assignment (NAME=value). Command lines start with a
# schedule field (or @reboot etc.), so they never match.
CRON_ASSIGN_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=(.*)$")


def mask_cron_line(line):
    """Mask a cron KEY=value assignment as `KEY=<masked, len N>`.

    N is the length of the value after stripping surrounding whitespace and
    one layer of matching quotes. Command lines are returned verbatim. This is
    the same contract as container env and env files: never the value.
    """
    line = line.rstrip()
    m = CRON_ASSIGN_RE.match(line)
    if not m:
        return line
    value = m.group(2).strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        value = value[1:-1]
    return f"{m.group(1)}=<masked, len {len(value)}>"


def cron_lines(text):
    """Non-blank, non-comment cron lines; assignments masked, commands verbatim."""
    return [mask_cron_line(ln) for ln in text.splitlines()
            if ln.strip() and not ln.lstrip().startswith("#")]


def collect_cron():
    c = json.loads(json.dumps(CRON_EMPTY))
    rc, out, err = run(["crontab", "-l"])
    if rc == 0:
        c["user"] = cron_lines(out)
    elif rc is None:
        warn(f"crontab -l: {err.strip()}")
    else:
        msg = (err or out).strip().splitlines()
        msg = msg[0] if msg else f"exit {rc}"
        if "no crontab" not in msg.lower():
            warn(f"crontab -l: {msg}")
    warn("root's crontab is not readable without sudo; not collected")

    txt = read_text("/etc/crontab") if os.path.exists("/etc/crontab") else ""
    if txt:
        c["system_crontab"] = cron_lines(txt)

    if os.path.isdir("/etc/cron.d"):
        try:
            names = sorted(os.listdir("/etc/cron.d"))
        except Exception as e:  # noqa: BLE001
            warn(f"cannot list /etc/cron.d: {e}")
            names = []
        for n in names:
            if n == ".placeholder" or n.startswith("."):
                continue
            p = os.path.join("/etc/cron.d", n)
            if not os.path.isfile(p):
                continue
            txt = read_text(p)
            if txt is None:
                continue
            c["cron_d"].append({"file": n, "lines": cron_lines(txt)})

    for period in ("hourly", "daily", "weekly", "monthly"):
        d = f"/etc/cron.{period}"
        if not os.path.isdir(d):
            continue
        try:
            c["periodic"][period] = sorted(n for n in os.listdir(d) if n != ".placeholder")
        except Exception as e:  # noqa: BLE001
            warn(f"cannot list {d}: {e}")
    return c


# --------------------------------------------------------------------------
# ollama
# --------------------------------------------------------------------------

def parse_table(out, columns):
    """Parse whitespace-separated table with a header; header detection by
    first column name. Columns beyond the last requested are joined."""
    rows = []
    lines = [ln for ln in out.splitlines() if ln.strip()]
    if not lines:
        return rows
    header = lines[0].split()
    if header and header[0].upper() == columns[0].upper():
        lines = lines[1:]
        # Determine column start offsets from the header text for robust
        # splitting (values like "2 hours ago" contain spaces).
        hdr = out.splitlines()[0] if out.splitlines() else ""
        offsets = []
        for col in columns:
            m = re.search(r"(?<!\S)" + re.escape(col) + r"(?!\S)", hdr, re.IGNORECASE)
            offsets.append(m.start() if m else None)
        if all(o is not None for o in offsets):
            for ln in [l for l in out.splitlines()[1:] if l.strip()]:
                row = {}
                for i, col in enumerate(columns):
                    start = offsets[i]
                    end = offsets[i + 1] if i + 1 < len(offsets) else None
                    row[col.lower()] = ln[start:end].strip()
                rows.append(row)
            return rows
    # Fallback: whitespace split, join remainder into last column.
    for ln in lines:
        parts = ln.split(None, len(columns) - 1)
        row = {}
        for i, col in enumerate(columns):
            row[col.lower()] = parts[i].strip() if i < len(parts) else ""
        rows.append(row)
    return rows


def collect_ollama():
    o = {"available": False, "error": None, "models": [], "running": []}
    if shutil.which("ollama") is None:
        o["error"] = "ollama: not found"
        return o
    rc, out, err = run(["ollama", "list"])
    if rc != 0:
        first = (err.strip() or out.strip()).splitlines()
        o["error"] = first[0] if first else f"ollama list: exit {rc}"
        return o
    o["available"] = True
    for r in parse_table(out, ["NAME", "ID", "SIZE", "MODIFIED"]):
        if not r.get("name"):
            continue
        o["models"].append({
            "name": r["name"], "id": r["id"], "size": r["size"], "modified": r["modified"],
        })
    rc, out, err = run(["ollama", "ps"])
    if rc != 0:
        first = (err.strip() or out.strip()).splitlines()
        warn(f"ollama ps: {first[0] if first else f'exit {rc}'}")
        return o
    for r in parse_table(out, ["NAME", "ID", "SIZE", "PROCESSOR", "UNTIL"]):
        if not r.get("name"):
            continue
        o["running"].append({
            "name": r["name"], "size": r["size"], "processor": r["processor"], "until": r["until"],
        })
    return o


# --------------------------------------------------------------------------
# files
# --------------------------------------------------------------------------

def collect_files(roots):
    f = {"roots": [], "largest": []}
    all_entries = []
    for root in roots:
        if not os.path.isdir(root):
            warn(f"files root missing: {root}")
            continue
        try:
            names = sorted(os.listdir(root))
        except Exception as e:  # noqa: BLE001
            warn(f"cannot list {root}: {e.__class__.__name__}: {e}")
            continue
        entries = []
        paths = []
        for n in names:
            p = os.path.join(root, n)
            try:
                st = os.lstat(p)
                kind = "dir" if os.path.isdir(p) and not os.path.islink(p) else "file"
                modified = _dt.datetime.fromtimestamp(st.st_mtime, tz=_dt.timezone.utc).isoformat()
            except Exception as e:  # noqa: BLE001
                warn(f"lstat {p}: {e.__class__.__name__}: {e}")
                kind, modified = "file", None
            entries.append({"name": n, "kind": kind, "size_bytes": None, "modified": modified})
            paths.append(p)

        sizes = {}
        if paths:
            # One du call per root with a 60 s budget; per-entry sizes come
            # back line by line. If it times out, sizes stay null.
            rc, out, err = run(["du", "-sb", "--apparent-size", "--"] + paths,
                               timeout=DU_TIMEOUT, label=f"du {root}")
            if rc is None:
                warn(f"du {root}: {err.strip() or 'failed'}; entry sizes recorded as null")
            else:
                if rc != 0 and err.strip():
                    # Typically permission-denied subdirectories; sizes are partial.
                    n_err = len(err.strip().splitlines())
                    warn(f"du {root}: {n_err} error line(s) (e.g. {err.strip().splitlines()[0]})")
                for ln in out.splitlines():
                    parts = ln.split("\t", 1)
                    if len(parts) == 2:
                        sizes[parts[1]] = to_int(parts[0])
        total = 0
        for e, p in zip(entries, paths):
            e["size_bytes"] = sizes.get(p)
            if e["size_bytes"] is not None:
                total += e["size_bytes"]
                all_entries.append({"path": p, "size_bytes": e["size_bytes"]})
        f["roots"].append({"path": root, "size_bytes": total if sizes else None, "entries": entries})

    all_entries.sort(key=lambda x: x["size_bytes"], reverse=True)
    f["largest"] = all_entries[:15]
    return f


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def main(argv=None):
    roots = resolve_roots(sys.argv[1:] if argv is None else argv)
    doc = {
        "schema": SCHEMA,
        "collected_at": _dt.datetime.now(tz=_dt.timezone.utc).isoformat(timespec="seconds"),
    }
    doc["host"] = section("host", collect_host, json.loads(json.dumps(HOST_EMPTY)))
    doc["disks"] = section("disks", collect_disks, [])
    doc["gpu"] = section("gpu", collect_gpu, {"available": False, "error": "section failed", "devices": []})
    doc["docker"] = section("docker", collect_docker, json.loads(json.dumps(DOCKER_EMPTY)))
    doc["env_files"] = section("env_files", lambda: collect_env_files(env_file_globs(roots)), [])
    doc["listening"] = section("listening", collect_listening, [])
    doc["systemd"] = section("systemd", collect_systemd, json.loads(json.dumps(SYSTEMD_EMPTY)))
    doc["cron"] = section("cron", collect_cron, json.loads(json.dumps(CRON_EMPTY)))
    doc["ollama"] = section("ollama", collect_ollama,
                            {"available": False, "error": "section failed", "models": [], "running": []})
    doc["files"] = section("files", lambda: collect_files(roots), {"roots": [], "largest": []})
    doc["warnings"] = WARNINGS
    return doc


if __name__ == "__main__":
    try:
        result = main()
    except Exception as e:  # noqa: BLE001
        result = {"schema": SCHEMA, "error": f"{e.__class__.__name__}: {e}", "warnings": WARNINGS}
    try:
        sys.stdout.write(json.dumps(result, ensure_ascii=False, default=str))
        sys.stdout.write("\n")
    except Exception as e:  # noqa: BLE001
        sys.stdout.write(json.dumps({"schema": SCHEMA, "error": f"serialise: {e}", "warnings": WARNINGS}))
        sys.stdout.write("\n")
    sys.stdout.flush()
