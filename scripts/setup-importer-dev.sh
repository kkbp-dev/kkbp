#!/usr/bin/env bash
# Creates importer/.venv from the Python inside the minimum Blender build and installs the pinned
# tools in importer/requirements-dev.txt into it. The venv runs the bundle/ tests on the exact
# Python the add-on runs on; nothing is installed into Blender's own Python.
#
# Usage: scripts/setup-importer-dev.sh
# The build is harness.toml's `min` (override with KKBP_BLENDER_MIN). Run it again after a
# Blender update: a venv whose Python has moved or changed version is rebuilt.
set -euo pipefail

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
venv="$repo/importer/.venv"

blender="$(python3 - "$repo" <<'PY'
import sys
sys.path.insert(0, sys.argv[1] + "/importer/tests/harness")
import run
print(run._builds(run._load_config(), ["min"])["min"]["path"])
PY
)"
python="$("$blender" --background --factory-startup --python-expr "import sys; print('KKBP_PY', sys.executable)" 2>/dev/null \
  | sed -n 's/^KKBP_PY //p')"
[[ -x "$python" ]] || { echo "setup-importer-dev: couldn't find the Python inside $blender" >&2; exit 1; }
want="$("$python" -c 'import sys; print(sys.version.split()[0])')"

if [[ -d "$venv" ]] && [[ "$("$venv/bin/python" -c 'import sys; print(sys.version.split()[0])' 2>/dev/null)" != "$want" ]]; then
  echo "== Rebuilding importer/.venv for Python $want"
  rm -rf "$venv"
fi
[[ -d "$venv" ]] || "$python" -m venv "$venv"

echo "== Installing importer/requirements-dev.txt into importer/.venv (Python $want from $blender)"
"$venv/bin/python" -m pip install --quiet --disable-pip-version-check -r "$repo/importer/requirements-dev.txt"
