"""SAF-2, SAF-3, SAF-5, DEP-5: the PreToolUse gate denies what it must and nothing else."""
import json
import subprocess

from devcli.paths import PLATFORM_ROOT

GATE = PLATFORM_ROOT / "hooks" / "platform-gate.sh"


def run(cmd: str, cwd: str = "/tmp") -> dict | None:
    p = subprocess.run(["bash", str(GATE)], input=json.dumps({"tool_name": "Bash", "tool_input": {"command": cmd}, "cwd": cwd}),
                       capture_output=True, text=True)
    assert p.returncode == 0
    return json.loads(p.stdout) if p.stdout.strip() else None


def denied(cmd, cwd="/tmp"):
    out = run(cmd, cwd)
    return out is not None and out["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_approve_is_denied_to_claude_but_verify_is_allowed():
    assert denied("dev approve prod")
    assert denied("cd x && dev approve prod")
    assert not denied("dev approve prod --verify")


def test_deploy_prod_without_approval_is_denied():
    assert denied("dev deploy prod")
    assert denied("./deploy/deploy.sh prod")
    assert denied("dev deploy prod; echo done")
    assert denied("cd x && dev deploy prod && echo done")


def test_deploy_dev_and_cert_pass():
    assert not denied("dev deploy dev")
    assert not denied("dev deploy cert")


def test_destructive_sql_denied_only_for_db_clients():
    assert denied("psql -c 'DROP TABLE users'")
    assert denied("psql -c 'DELETE FROM orders'")
    assert denied("sqlcmd -Q \"UPDATE t SET x=1\"")
    assert not denied("psql -c 'DELETE FROM orders WHERE id = 3'")
    assert not denied("grep -r 'DROP TABLE' docs/")
    assert not denied("ls -la")
