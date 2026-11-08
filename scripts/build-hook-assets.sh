#!/usr/bin/env bash
# Builds the built-in Hooks' asset files (rigify.blend, face_cards.blend, outlines.blend in
# importer/kkbp/library/) from the legacy importer/templates-src/KK Shader V9.blend with
# importer/tools/build_hook_assets.py (D15, ADR 0018). Runs on the harness's minimum Blender build;
# review the diff of the script, not the .blend files.
#
# Usage: scripts/build-hook-assets.sh
set -euo pipefail
repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
blender="${KKBP_BLENDER_MIN:-$(python3 -c 'import tomllib,sys; print(tomllib.load(open(sys.argv[1],"rb"))["blender"]["min"]["path"])' "$repo/importer/tests/harness/harness.toml")}"
source="$repo/importer/templates-src/KK Shader V9.blend"
"$blender" --background --factory-startup --python-exit-code 1 \
  --python "$repo/importer/tools/build_hook_assets.py" -- "$source"
ls -l "$repo"/importer/kkbp/library/{rigify,face_cards,outlines}.blend
