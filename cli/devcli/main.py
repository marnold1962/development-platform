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

    pl = sub.add_parser("platform", help="platform maintenance")
    pls = pl.add_subparsers(dest="pcmd", required=True)
    u = pls.add_parser("update", help="pull the platform and install agents, skills and commands to ~/.claude")
    u.add_argument("--no-pull", action="store_true", help="install from the working copy without git pull")

    for name in ("list", "status", "deploy", "health", "rollback", "db"):
        sub.add_parser(name, help="increment 2")
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
            return commands.open_(args.project, args.check)
        if args.cmd == "platform" and args.pcmd == "update":
            return commands.platform_update(pull=not args.no_pull)
        raise DevError(f"'dev {args.cmd}' arrives in increment 2", 2)
    except DevError as e:
        sys.stdout.flush()
        print(f"error: {e}", file=sys.stderr, flush=True)
        return e.code
    except KeyboardInterrupt:
        print("error: interrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
