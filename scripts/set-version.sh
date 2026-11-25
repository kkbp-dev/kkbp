#!/usr/bin/env bash
# Sets the KKBP Version (ADR 0060), the release date as YYYY.MM.DD that the importer and the
# exporters share. It writes the repository's VERSION file, which the exporter build reads, and the
# importer's blender_manifest.toml, which holds the same date without leading zeros (2027.01.05 is
# 2027.1.5 there) because Blender only accepts strict semantic versions.
#
# Usage: scripts/set-version.sh [YYYY.MM.DD]   (default: today)
set -euo pipefail

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
manifest="$repo/importer/kkbp/blender_manifest.toml"

[[ $# -le 1 ]] || { sed -n '2,7p' "$0" | sed 's/^# \{0,1\}//'; exit 1; }
version="${1:-$(date +%Y.%m.%d)}"

[[ "$version" =~ ^([0-9]{4})\.([0-9]{2})\.([0-9]{2})$ ]] \
  || { echo "set-version: '$version' isn't YYYY.MM.DD" >&2; exit 1; }
year="${BASH_REMATCH[1]}" month="${BASH_REMATCH[2]}" day="${BASH_REMATCH[3]}"
[[ "$(date -d "$year-$month-$day" +%Y.%m.%d 2>/dev/null)" == "$version" ]] \
  || { echo "set-version: '$version' isn't a real date" >&2; exit 1; }
plain="$((10#$year)).$((10#$month)).$((10#$day))"

grep -q '^version = ' "$manifest" || { echo "set-version: no version line in $manifest" >&2; exit 1; }
printf '%s\n' "$version" > "$repo/VERSION"
sed -i "s/^version = .*/version = \"$plain\"/" "$manifest"
echo "KKBP Version $version (Blender and BepInEx: $plain)"
