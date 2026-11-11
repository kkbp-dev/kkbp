#!/usr/bin/env bash
# Checks that the committed library and Hook asset files are what their sources build (ADR 0040):
# builds them into importer/tests/.work/library-check/, fingerprints both, and lists every
# difference. Exits 1 if there is one.
#
# Usage: scripts/check-library.sh [library|rigify|face_cards|outlines ...]
set -euo pipefail
repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
blender="${KKBP_BLENDER_MIN:-$(python3 -c 'import tomllib,sys; print(tomllib.load(open(sys.argv[1],"rb"))["blender"]["min"]["path"])' "$repo/importer/tests/harness/harness.toml")}"
tools="$repo/importer/tools/library"
work="$repo/importer/tests/.work/library-check"
files="${*:-library rigify face_cards outlines}"
mkdir -p "$work"
"$blender" --background --factory-startup --python-exit-code 1 --python "$tools/build.py" -- --out "$work" $files
status=0
for f in $files; do
  for side in committed built; do
    blend="$repo/importer/kkbp/library/$f.blend"; [[ $side = built ]] && blend="$work/$f.blend"
    "$blender" --background --factory-startup --python-exit-code 1 "$blend" \
      --python "$tools/fingerprint.py" -- "$work/$f.$side.json" > /dev/null
  done
  echo "== $f"
  python3 "$tools/compare.py" "$work/$f.committed.json" "$work/$f.built.json" || status=1
done
exit $status
