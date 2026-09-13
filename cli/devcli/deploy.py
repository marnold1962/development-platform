"""dev deploy / approve / rollback / health / status / list / db inspect (increment 2).

Policy lives here; transport in remote.py; the host-side steps in scripts/deployment/remote.
"""
import datetime as dt
import json
import subprocess
from pathlib import Path

from devcli import gitops, remote
from devcli.config import load_profile, load_registry, load_target
from devcli.errors import DevError
from devcli.paths import IDENTITY_ROOTS, PLATFORM_ROOT

ENVS = ("dev", "cert", "prod")


# ------------------------------------------------------------------ helpers
def _project(path: Path) -> tuple[dict, dict]:
    profile = load_profile(path)
    target = load_target(path)
    if target["kind"] != "service":
        raise DevError(f"{profile['name']} is kind '{target['kind']}'; only services deploy (TPL-3)", 2)
    return profile, target


def _env(target: dict, env: str) -> dict:
    if env not in ENVS or env not in target.get("environments", {}):
        raise DevError(f"environment '{env}' not in deploy/target.yml", 2)
    return target["environments"][env]


def _head(project: Path) -> str:
    return gitops.run(["git", "rev-parse", "HEAD"], project).stdout.strip()


def _repo_name(project: Path) -> str:
    return project.name


def _connect(target: dict) -> tuple[str, dict]:
    entry = remote.host_entry(load_registry("environments"), target["host"])
    alias = remote.pick_ssh(entry)
    remote.install_remote(alias, entry["deploy_root"])
    return alias, entry


def _mounts_spec(target: dict, entry: dict) -> str:
    """'host:container:ro,...' for the remote script. Host paths must sit under the host's deploy_root (DEP-10)."""
    specs = []
    for m in target.get("mounts", []):
        if not m["host"].startswith(entry["deploy_root"].rstrip("/") + "/") and m["host"] != entry["deploy_root"]:
            raise DevError(f"mount {m['host']} is outside the host deploy_root {entry['deploy_root']}; refused (DEP-10)", 2)
        specs.append(f"{m['host']}:{m['container']}:{'ro' if m.get('readonly', True) else 'rw'}")
    return ",".join(specs)


def _approval_path(project: Path, env: str) -> Path:
    return project / ".platform" / f"approval-{env}.json"


def _local_record(project: Path, entry: dict) -> None:
    d = project / ".platform"
    d.mkdir(exist_ok=True)
    with (d / "deployments.jsonl").open("a") as f:
        f.write(json.dumps(entry) + "\n")


# ------------------------------------------------------------------ preconditions
def _preflight(project: Path, profile: dict, target: dict, env: str, run_tests: bool) -> str:
    """DEP-1, DEP-3, DEP-4: clean tree, on the env branch, tests. Returns HEAD sha."""
    g = gitops.state(project)
    if not g["repo"]:
        raise DevError("not a git repository", 2)
    if g["dirty"]:
        raise DevError(f"working tree is dirty ({g['dirty']} files); commit or stash before deploying", 2)
    branch = _env(target, env)["branch"]
    if g["branch"] != branch:
        raise DevError(f"deploy {env} requires branch '{branch}' checked out; current is '{g['branch']}' (DEP-1)", 2)
    sha = _head(project)
    print(f"preflight: repo {_repo_name(project)} branch {branch} commit {sha[:12]} clean")
    if run_tests:
        print("tests: make test")
        r = subprocess.run(["make", "test"], cwd=project, capture_output=True, text=True)
        tail = "\n".join((r.stdout + r.stderr).strip().splitlines()[-3:])
        if r.returncode != 0:
            raise DevError(f"tests failed; not deploying:\n{tail}", 1)
        print("tests: " + tail.splitlines()[-1])
    return sha


def _migrations_since_last_prod(project: Path) -> list[str]:
    last = None
    f = project / ".platform" / "deployments.jsonl"
    if f.exists():
        for line in f.read_text().splitlines():
            e = json.loads(line)
            if e.get("env") == "prod" and e.get("ok"):
                last = e["sha"]
    rng = f"{last}..HEAD" if last else "HEAD"
    r = gitops.run(["git", "diff", "--name-only", rng, "--", "migrations"], project, check=False) if last else \
        gitops.run(["git", "ls-files", "migrations"], project, check=False)
    return [l for l in r.stdout.splitlines() if l and not l.endswith(".gitkeep")]


# ------------------------------------------------------------------ approve (human only; the gate hook denies it to Claude)
def approve(project: Path, env: str, verify_only: bool) -> int:
    profile, target = _project(project)
    if env != "prod":
        raise DevError("approval is only required for prod", 2)
    ap = _approval_path(project, env)
    sha = _head(project)
    if verify_only:
        if not ap.exists():
            raise DevError("no prod approval on file (run: dev approve prod)", 4)
        a = json.loads(ap.read_text())
        want = {"repo": _repo_name(project), "commit": sha, "branch": _env(target, env)["branch"], "env": env, "target": target["host"]}
        if {k: a.get(k) for k in want} != want:
            raise DevError(f"prod approval does not match HEAD: approved {a.get('commit', '')[:12]}, HEAD {sha[:12]} (DEP-6)", 4)
        print(f"approval valid for {sha[:12]} by {a['by']} at {a['time']}")
        return 0
    g = gitops.state(project)
    if g["dirty"]:
        raise DevError("working tree is dirty; approve a committed state", 2)
    branch = _env(target, env)["branch"]
    if g["branch"] != branch:
        raise DevError(f"approve prod from branch '{branch}'; current is '{g['branch']}'", 2)
    migs = _migrations_since_last_prod(project)
    print("PRODUCTION APPROVAL — type each value exactly (DEP-5).")
    print(f"  repo    : {_repo_name(project)}\n  commit  : {sha}\n  branch  : {branch}\n  env     : {env}\n  target  : {target['host']}")
    print("  migrations since last prod deploy: " + (", ".join(migs) if migs else "none"))
    typed = input("Type the first 12 characters of the commit to approve: ").strip()
    if typed != sha[:12]:
        raise DevError("approval refused: commit mismatch", 2)
    backup = input("Backup/snapshot taken or not needed? state it: ").strip()
    rollback = input("Rollback plan (default: dev rollback prod): ").strip() or "dev rollback prod"
    if migs:
        rv = input("Migrations reviewed? type REVIEWED: ").strip()
        if rv != "REVIEWED":
            raise DevError("approval refused: migrations not reviewed", 2)
    a = {"repo": _repo_name(project), "commit": sha, "branch": branch, "env": env, "target": target["host"],
         "migrations": migs, "backup": backup, "rollback": rollback,
         "by": gitops.signing_email(project), "time": dt.datetime.now().isoformat(timespec="seconds")}
    ap.parent.mkdir(exist_ok=True)
    ap.write_text(json.dumps(a, indent=2) + "\n")
    print(f"approved {sha[:12]} for prod; lapses when HEAD changes")
    return 0


# ------------------------------------------------------------------ deploy
def deploy(project: Path, env: str) -> int:
    profile, target = _project(project)
    _env(target, env)
    sha = _preflight(project, profile, target, env, run_tests=True)
    if env == "prod":
        approve(project, env, verify_only=True)
        a = json.loads(_approval_path(project, env).read_text())
        print(f"prod checks: backup='{a['backup']}' rollback='{a['rollback']}' migrations={a['migrations'] or 'none'}")
    alias, entry = _connect(target)
    name = profile["name"]
    bare = remote.remote(alias, entry, "receive", name, env).stdout.strip().splitlines()[-1]
    branch = _env(target, env)["branch"]
    print(f"push: {branch} -> {alias}:{bare}")
    gitops.run(["git", "push", "-q", f"ssh://{alias}{bare}", f"HEAD:refs/heads/{branch}"], project)
    print(f"deploy: {name} {env} {sha[:12]} on {alias}")
    r = remote.remote(alias, entry, "deploy", name, env, sha, _mounts_spec(target, entry), check=False)
    print((r.stdout + r.stderr).rstrip())
    ok = r.returncode == 0
    rec = {"time": dt.datetime.now().isoformat(timespec="seconds"), "env": env, "sha": sha, "ok": ok, "host": target["host"]}
    if env == "prod":
        rec["approval"] = json.loads(_approval_path(project, env).read_text())
        _approval_path(project, env).unlink()  # one approval, one deploy
    _local_record(project, rec)
    if not ok:
        raise DevError(f"deploy {env} failed health check; see log above. Rollback: dev rollback {env}", 1)
    print(f"deployed {name} {env} {sha[:12]}; url on host: http://127.0.0.1:{entry['router_port']}/platform/{env}/{name}/")
    return 0


def rollback(project: Path, env: str) -> int:
    profile, target = _project(project)
    _env(target, env)
    alias, entry = _connect(target)
    r = remote.remote(alias, entry, "rollback", profile["name"], env, "-", _mounts_spec(target, entry), check=False)
    print((r.stdout + r.stderr).rstrip())
    if r.returncode != 0:
        raise DevError(f"rollback {env} refused or failed", r.returncode)
    _local_record(project, {"time": dt.datetime.now().isoformat(timespec="seconds"), "env": env, "ok": True, "rollback": True, "host": target["host"]})
    return 0


def health(project: Path, env: str | None) -> int:
    profile, target = _project(project)
    envs = [env] if env else [e for e in ENVS if e in target.get("environments", {})]
    alias, entry = _connect(target)
    print(f"tunnel/ssh: {alias} reachable")
    bad = 0
    for e in envs:
        r = remote.remote(alias, entry, "health", profile["name"], e, check=False)
        print(f"--- {e}\n" + (r.stdout + r.stderr).rstrip())
        bad += r.returncode != 0
    if bad:
        raise DevError(f"{bad} environment(s) unhealthy", 1)
    return 0


def status(project: Path, offline: bool) -> int:
    from devcli import session
    profile = load_profile(project)
    target = load_target(project)
    s = session.build(project, profile, target)
    print(session.render(s))
    if target["kind"] == "service" and not offline:
        try:
            alias, entry = _connect(target)
            r = remote.remote(alias, entry, "status", profile["name"], check=False)
            print("\nDEPLOYMENTS (from host)")
            print((r.stdout or "none").rstrip())
        except DevError as e:
            print(f"\nDEPLOYMENTS: host unreachable ({e})")
    return 0


def list_projects() -> int:
    rows = []
    for ident, root in IDENTITY_ROOTS.items():
        if not root.is_dir():
            continue
        for d in sorted(root.iterdir()):
            pf = d / "project" / "profile.yaml"
            if not pf.exists():
                continue
            try:
                p = load_profile(d); t = load_target(d)
                rows.append((p["name"], ident, t["kind"], t.get("host", "-"), "ok"))
            except DevError as e:
                rows.append((d.name, ident, "?", "?", "invalid: " + str(e).split(":")[-1].strip()))
    if not rows:
        print("no platform projects found under " + ", ".join(str(r) for r in IDENTITY_ROOTS.values()))
        return 0
    w = max(len(r[0]) for r in rows)
    for r in rows:
        print(f"{r[0]:<{w}}  {r[1]:<7}  {r[2]:<8}  {r[3]:<8}  {r[4]}")
    return 0


def db_inspect(project: Path, name: str) -> int:
    profile = load_profile(project)
    declared = {d["name"]: d["access"] for d in profile.get("data_sources", [])}
    if name != "app" and name not in declared:
        raise DevError(f"'{name}' is not declared in project/profile.yaml data_sources", 2)
    if name != "app":
        dbs = load_registry("databases")["databases"]
        if name not in dbs:
            raise DevError(f"'{name}' is not in registries/databases.yaml; register it from inspection first (REG-5)", 2)
        print(f"{name}: access {declared[name]} (declared), registry engine {dbs[name]['engine']} on {dbs[name]['host']}")
    env = {}
    envfile = project / ".env"
    if envfile.exists():
        for line in envfile.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, _, v = line.partition("="); env[k.strip()] = v.strip()
    import os
    r = subprocess.run([str(project / ".venv" / "bin" / "python") if (project / ".venv").exists() else "python3",
                        str(PLATFORM_ROOT / "scripts" / "database" / "inspect-schema.py"), name],
                       cwd=project, env={**os.environ, **env}, capture_output=True, text=True)
    print((r.stdout + r.stderr).rstrip())
    return r.returncode
