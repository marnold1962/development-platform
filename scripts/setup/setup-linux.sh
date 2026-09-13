#!/usr/bin/env bash
# Verify a Linux workstation has what the platform needs. Installs nothing; reports.
set -u
ok=0; bad=0
check () { if command -v "$1" >/dev/null 2>&1; then echo "ok    $1"; ok=$((ok+1)); else echo "MISSING $1  ($2)"; bad=$((bad+1)); fi; }
[ "$(uname -s)" = "Linux" ] || { echo "This platform supports Linux only (Q7)."; exit 2; }
check git "git"
check gh "GitHub CLI"
check claude "Claude Code"
check python3 "Python 3.12+"
check docker "Docker (only needed for service deploys)"
gh auth status >/dev/null 2>&1 && echo "ok    gh authenticated" || { echo "MISSING gh authentication (run: gh auth login)"; bad=$((bad+1)); }
echo "$ok ok, $bad missing"
[ "$bad" -eq 0 ]
