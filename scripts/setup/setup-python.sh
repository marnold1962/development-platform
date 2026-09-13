#!/usr/bin/env bash
# Create the platform's own virtualenv for the dev CLI.
set -eu
here="$(cd "$(dirname "$0")/../.." && pwd)"
python3 -m venv "$here/.venv"
"$here/.venv/bin/python" -m pip install -q --upgrade pip
"$here/.venv/bin/python" -m pip install -q -e "$here/cli[dev]"
mkdir -p "$HOME/.local/bin"
ln -sf "$here/cli/bin/dev" "$HOME/.local/bin/dev"
echo "dev CLI installed: $(command -v dev)"
