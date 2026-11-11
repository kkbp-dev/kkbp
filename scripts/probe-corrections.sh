#!/usr/bin/env bash
# Records what a game's joint corrections do to its Sample Card, for the importer's tests
# (docs/design/joint-corrections.md): deploys the exporter, runs its correction probe on the poses
# from importer/tools/correction_poses.py, and writes importer/tests/data/corrections/<game>.json.gz.
# It starts the game, so it refuses to run while the game is open.
#
# Usage: scripts/probe-corrections.sh kk|kks|svs [copy of the untrimmed probe output]
set -euo pipefail

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
game="${1:-}"
case "$game" in kk|kks|svs) ;; *) sed -n '2,7p' "$0" | sed 's/^# \{0,1\}//'; exit 1 ;; esac

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
winpath() { printf 'Z:%s' "${1//\//\\\\}"; }

python3 "$repo/importer/tools/correction_poses.py" "$game" "$work/poses.json"
"$repo/scripts/deploy-exporter.sh" "$game" >/dev/null
"$repo/scripts/auto-export.sh" "$game" "$repo/contract/sample-cards/$game.png" "$work/out" \
  "\"probe_corrections\": \"$(winpath "$work/raw.json")\", \"probe_poses\": \"$(winpath "$work/poses.json")\""
mkdir -p "$repo/importer/tests/data/corrections"
python3 "$repo/importer/tools/correction_poses.py" --trim "$game" "$work/raw.json" "$repo/importer/tests/data/corrections/$game.json.gz"
if [[ -n "${2:-}" ]]; then cp "$work/raw.json" "$2"; fi
echo "Wrote importer/tests/data/corrections/$game.json.gz"
