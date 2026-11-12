#!/usr/bin/env bash
# Writes node groups and materials of a .blend back to their modules in importer/tools/library/
# (ADR 0040): after editing a group in Blender, save the file and run this, then review the module
# diff and rebuild with scripts/build-library.sh. With no names, every group and material in the file.
#
# Usage: scripts/export-library-nodes.sh FILE.blend [NAME ...]
set -euo pipefail
repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
[[ $# -ge 1 ]] || { echo "usage: scripts/export-library-nodes.sh FILE.blend [NAME ...]" >&2; exit 2; }
blender="${KKBP_BLENDER_MIN:-$(python3 -c 'import tomllib,sys; print(tomllib.load(open(sys.argv[1],"rb"))["blender"]["min"]["path"])' "$repo/importer/tests/harness/harness.toml")}"
file="$1"; shift
"$blender" --background --factory-startup --python-exit-code 1 "$file" \
  --python "$repo/importer/tools/library/export_nodes.py" -- "$repo/importer/tools/library" "$@"
git -C "$repo" status --short importer/tools/library/groups importer/tools/library/materials
