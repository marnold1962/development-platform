#!/usr/bin/env bash
# Platform risk gate. PreToolUse hook for Bash. Reads the tool call as JSON on stdin.
# Denies: `dev approve` (human only); `dev deploy prod` / `deploy.sh prod` without a valid
# approval for HEAD; destructive SQL patterns handed to a database CLI.
# Exit 0 with a JSON decision. Never blocks anything else.
input=$(cat)
cmd=$(printf '%s' "$input" | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get("tool_input",{}).get("command",""))' 2>/dev/null || true)
cwd=$(printf '%s' "$input" | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get("cwd",""))' 2>/dev/null || true)
deny() { printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"%s"}}\n' "$1"; exit 0; }

if printf '%s' "$cmd" | grep -Eq '(^|[;&| ])dev[[:space:]]+approve([[:space:];&|]|$)' && ! printf '%s' "$cmd" | grep -Eq -- '--verify'; then
  deny "platform gate: dev approve is for the human only. Ask the user to run it with the ! prefix."
fi
if printf '%s' "$cmd" | grep -Eq '(^|[;&| ])(dev[[:space:]]+deploy[[:space:]]+prod|\./?deploy/deploy\.sh[[:space:]]+prod|deploy\.sh[[:space:]]+prod)([[:space:];&|]|$)'; then
  DEV_BIN=$(command -v dev 2>/dev/null || echo "$HOME/.local/bin/dev")
  # A command that starts with `cd <dir> &&` is checked in that dir, not the session cwd.
  lead=$(printf '%s' "$cmd" | sed -nE 's/^[[:space:]]*cd[[:space:]]+([^&;|[:space:]]+)[[:space:]]*(&&|;).*/\1/p' | head -1)
  case "$lead" in "~"*) lead="$HOME${lead#\~}";; esac
  [ -n "$lead" ] && cwd="$lead"
  if ! (cd "${cwd:-.}" 2>/dev/null && "$DEV_BIN" approve prod --verify >/dev/null 2>&1); then
    deny "platform gate: no valid prod approval for HEAD. The user must run: dev approve prod"
  fi
fi
if printf '%s' "$cmd" | grep -Eiq '(psql|sqlcmd|mysql|clickhouse-client|sqlite3)' ; then
  if printf '%s' "$cmd" | grep -Eiq '\b(drop[[:space:]]+(table|database|schema)|truncate[[:space:]]+table)\b'; then
    deny "platform gate: DROP/TRUNCATE outside a reviewed migration is refused (SAF-3)."
  fi
  if printf '%s' "$cmd" | grep -Eiq '\b(delete[[:space:]]+from|update)[[:space:]]+[a-z_."]+([[:space:]]+set[[:space:]]+[^;]*)?;?' && ! printf '%s' "$cmd" | grep -Eiq '\bwhere\b'; then
    deny "platform gate: unscoped DELETE/UPDATE is refused (SAF-2). Add a WHERE clause."
  fi
fi
exit 0
