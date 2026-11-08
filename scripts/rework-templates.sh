#!/usr/bin/env bash
# Builds the importer's Material Template library, importer/kkbp/library/library.blend, from the
# legacy importer/templates-src/KK Shader V9.blend with importer/tools/rework_templates.py
# (ADR 0018). Runs on the harness's minimum Blender build; review the diff of the script, not the .blend.
#
# Usage: scripts/rework-templates.sh
set -euo pipefail
repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
blender="${KKBP_BLENDER_MIN:-$(python3 -c 'import tomllib,sys; print(tomllib.load(open(sys.argv[1],"rb"))["blender"]["min"]["path"])' "$repo/importer/tests/harness/harness.toml")}"
source="$repo/importer/templates-src/KK Shader V9.blend"
output="$repo/importer/kkbp/library/library.blend"
mkdir -p "$(dirname "$output")"
"$blender" --background --factory-startup --python-exit-code 1 \
  --python "$repo/importer/tools/rework_templates.py" -- "$source" "$output"
rm -f "$output"1  # Blender's backup of the previous library
ls -l "$output"
