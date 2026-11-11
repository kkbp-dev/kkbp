#!/usr/bin/env bash
# Builds the importer's Material Template library and the built-in Hooks' asset files
# (library.blend, rigify.blend, face_cards.blend, outlines.blend in importer/kkbp/library/) from
# importer/tools/library/ and importer/library-src/ (ADR 0040). Runs on the harness's minimum
# Blender build; review the diff of the modules and source files, not the .blend files.
#
# Usage: scripts/build-library.sh [library|rigify|face_cards|outlines ...]
set -euo pipefail
repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
blender="${KKBP_BLENDER_MIN:-$(python3 -c 'import tomllib,sys; print(tomllib.load(open(sys.argv[1],"rb"))["blender"]["min"]["path"])' "$repo/importer/tests/harness/harness.toml")}"
"$blender" --background --factory-startup --python-exit-code 1 \
  --python "$repo/importer/tools/library/build.py" -- "$@"
ls -l "$repo"/importer/kkbp/library/*.blend
