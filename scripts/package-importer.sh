#!/usr/bin/env bash
# Builds the importer extension into an installable zip, importer/dist/kkbp-<version>.zip, with
# Blender's own extension builder on the harness's minimum build. The zip holds importer/kkbp/ as
# it is in the working tree, without caches or downloaded Pillow wheels, and the repository's
# LICENSE and NOTICE. Install it in Blender with Preferences > Get Extensions > Install from Disk.
#
# Usage: scripts/package-importer.sh
set -euo pipefail
repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# harness.toml's `min` build, or KKBP_BLENDER_MIN, resolved the way the harness does (~ expanded).
blender="$(python3 -c 'import sys; sys.path.insert(0, sys.argv[1]); import run; print(run._builds(run._load_config(), ["min"])["min"]["path"])' "$repo/importer/tests/harness")"
source="$repo/importer/kkbp"
dist="$repo/importer/dist"

# The asset files are in Git LFS; a pointer file instead of a .blend means `git lfs pull` hasn't run.
for blend in "$source"/library/*.blend; do
  if head -c 64 "$blend" | grep -q "git-lfs"; then
    echo "package-importer: $blend is a Git LFS pointer; run git lfs pull" >&2
    exit 1
  fi
done

stage="$(mktemp -d)"
trap 'rm -rf "$stage"' EXIT
mkdir -p "$stage/kkbp" "$dist"
(cd "$source" && find . -type f ! -path "*/__pycache__/*" ! -path "./wheels/*" ! -name "*.blend1" -print0 \
  | xargs -0 -I{} cp --parents {} "$stage/kkbp/")
cp "$repo/LICENSE" "$repo/NOTICE" "$stage/kkbp/"
"$blender" --factory-startup --command extension build --source-dir "$stage/kkbp" --output-dir "$dist"
ls -l "$dist"
