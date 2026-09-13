#!/usr/bin/env bash
# Validate that a data source is reachable. Usage: check-db.sh <logical-name>
set -u
exec python3 "$(dirname "$0")/inspect-schema.py" "$1" >/dev/null && echo "reachable: $1" || { echo "unreachable: $1"; exit 3; }
