"""Entry point. One user-facing command: dev (CLI-1). Exit codes per CLI-14."""
import argparse
import sys

from devcli import commands
from devcli.errors import DevError


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="dev", description="Development platform ignition key.")
    sub = p.add_subparsers(dest="cmd", required=True)

    n = sub.add_parser("new", help="create a project: dev new <type> <target>")
    n.add_argument("type", help="flask (increment 1)")
    n.add_argument("target", help="hosting target from registries/environments.yaml, e.g. as2")
    n.add_argument("--name"); n.add_argument("--purpose")
    n.add_argument("--branches", help="comma list for dev,cert,prod")
    n.add_argument("--data-source", action="append", default=[], help="name:access, repeatable")
    n.add_argument("--identity", choices=["as2", "company"], default="as2")
    n.add_argument("--non-interactive", action="store_true", help="default every unanswered item")
    n.add_argument("--local", action="store_true", help="do not create the GitHub repository")
    n.add_argument("--no-launch", action="store_true", help="do not start Claude Code afterwards")

    o = sub.add_parser("open", help="open a project: dev open <name|path>")
    o.add_argument("project")
    o.add_argument("--check", action="store_true", help="verify and print the readiness summary; do not launch")
    o.add_argument("--adopt", action="store_true", help="adopt a repository the platform did not create (increment 3)")
    o.add_argument("--name"); o.add_argument("--purpose")
    o.add_argument("--kind", choices=["service", "desktop"])
    o.add_argument("--host", default="as2", help="hosting target for an adopted service")
    o.add_argument("--branches", help="comma list for dev,cert,prod")
    o.add_argument("--non-interactive", action="store_true")

    pl = sub.add_parser("platform", help="platform maintenance")
    pls = pl.add_subparsers(dest="pcmd", required=True)
    u = pls.add_parser("update", help="pull the platform and install agents, skills and commands to ~/.claude")
    u.add_argument("--no-pull", action="store_true", help="install from the working copy without git pull")

    sub.add_parser("list", help="platform projects under the identity folders")
    st = sub.add_parser("status", help="readiness summary plus last deployment per environment")
    st.add_argument("--offline", action="store_true", help="do not contact the host")
    d = sub.add_parser("deploy", help="dev deploy <env>: preflight, tests, push to host, build, run, health-check")
    d.add_argument("env", choices=["dev", "cert", "prod"])
    ap = sub.add_parser("approve", help="human only: approve the current HEAD for prod (dev approve prod)")
    ap.add_argument("env", choices=["prod"])
    ap.add_argument("--verify", action="store_true", help="check that a valid approval exists for HEAD; exit 4 if not")
    h = sub.add_parser("health", help="dev health [env]: router, container and healthz on the host")
    h.add_argument("env", nargs="?", choices=["dev", "cert", "prod"])
    rb = sub.add_parser("rollback", help="dev rollback <env>: re-run the previous successful deployment")
    rb.add_argument("env", choices=["dev", "cert", "prod"])
    db = sub.add_parser("db", help="database operations")
    dbs = db.add_subparsers(dest="dbcmd", required=True)
    di = dbs.add_parser("inspect", help="dev db inspect <name>: validate and inspect a declared data source")
    di.add_argument("name", nargs="?", default="app")
    ho = sub.add_parser("host", help="host operations")
    hos = ho.add_subparsers(dest="hcmd", required=True)
    hi = hos.add_parser("inventory", help="dev host inventory <host>: read-only report of everything on the host, rendered to HTML")
    hi.add_argument("host", help="host from registries/environments.yaml, e.g. as2")
    hi.add_argument("--out", help="output directory (default ~/Work/inventory/<host>)")
    hi.add_argument("--no-open", action="store_true", help="do not open the report in the browser")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.cmd == "new":
            answers = {}
            if args.name: answers["name"] = args.name
            if args.purpose: answers["purpose"] = args.purpose
            if args.branches: answers["branches"] = [b.strip() for b in args.branches.split(",")]
            if args.data_source: answers["data_sources"] = args.data_source
            answers["identity"] = args.identity
            return commands.new(args.type, args.target, answers, not args.non_interactive, not args.local, not args.no_launch)
        if args.cmd == "open":
            aa = {}
            if args.name: aa["name"] = args.name
            if args.purpose: aa["purpose"] = args.purpose
            if args.kind: aa["kind"] = args.kind
            if args.branches: aa["branches"] = [b.strip() for b in args.branches.split(",")]
            return commands.open_(args.project, args.check, args.adopt, aa, not args.non_interactive, args.host)
        if args.cmd == "platform" and args.pcmd == "update":
            return commands.platform_update(pull=not args.no_pull)
        if args.cmd == "host" and args.hcmd == "inventory":
            from pathlib import Path
            from devcli import inventory
            inventory.run(args.host, Path(args.out) if args.out else None, not args.no_open)
            return 0
        from devcli import deploy as dp
        from devcli.commands import _find_project
        if args.cmd == "list":
            return dp.list_projects()
        here = _find_project(".")
        if args.cmd == "status":
            return dp.status(here, args.offline)
        if args.cmd == "deploy":
            return dp.deploy(here, args.env)
        if args.cmd == "approve":
            return dp.approve(here, args.env, args.verify)
        if args.cmd == "health":
            return dp.health(here, args.env)
        if args.cmd == "rollback":
            return dp.rollback(here, args.env)
        if args.cmd == "db" and args.dbcmd == "inspect":
            return dp.db_inspect(here, args.name)
        raise DevError(f"unknown command {args.cmd}", 2)
    except DevError as e:
        sys.stdout.flush()
        print(f"error: {e}", file=sys.stderr, flush=True)
        return e.code
    except KeyboardInterrupt:
        print("error: interrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
