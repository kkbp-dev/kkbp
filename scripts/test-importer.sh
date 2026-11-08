#!/usr/bin/env bash
# Runs the importer's tests: the host tests (bundle/, profiles/, library/ and source rules) and the
# harness's own unit tests on importer/.venv's Python, which is Blender's own interpreter; then the
# in-Blender tests on every harness build in an isolated profile; then the Core Import of every
# Golden Sample on every build, the same with every built-in Hook, and each Hook on its own (each
# fails if an import or a Hook fails, or a Hook changes what it doesn't own). Needs
# scripts/setup-importer-dev.sh to have run once, and the Golden Samples from
# scripts/export-sample.sh; tests of a Game with no Golden Sample are skipped, with a notice.
#
# Usage: scripts/test-importer.sh [--host-only | --blender-only] [pytest arguments]
set -euo pipefail

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python="$repo/importer/.venv/bin/python"
[[ -x "$python" ]] || { echo "test-importer: run scripts/setup-importer-dev.sh first" >&2; exit 1; }
source "$repo/scripts/golden-samples.sh"
golden_report

host=1 blender=1
case "${1:-}" in
  --host-only) blender=0; shift ;;
  --blender-only) host=0; shift ;;
esac

if (( host )); then
  echo "== Host tests"
  "$python" -m pytest -q -p no:cacheprovider "$repo/importer/tests/host" "$@"
  echo "== Harness unit tests"
  "$python" -m unittest discover -s "$repo/importer/tests/harness" -t "$repo/importer/tests/harness" 2>&1 | tail -n 3
fi
if (( blender )); then
  "$python" "$repo/importer/tests/blender/launch.py" "$@"
  if (( $# == 0 )); then
    echo "== Golden samples, Core Import"
    "$python" "$repo/importer/tests/harness/run.py" core
    echo "== Golden samples, built-in Hooks"
    "$python" "$repo/importer/tests/harness/run.py" hooks
    echo "== Golden samples, each built-in Hook on its own"
    "$python" "$repo/importer/tests/harness/run.py" hooks --each
  fi
fi
