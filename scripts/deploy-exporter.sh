#!/usr/bin/env bash
# Builds one Game Adapter and copies it, with the repository's LICENSE and NOTICE, into that game's
# BepInEx plugins folder, as <game>/BepInEx/plugins/KKBP/. The install is games/ in the working
# copy, or KKBP_GAMES_DIR.
#
# Usage: scripts/deploy-exporter.sh kk|kks|svs
set -euo pipefail

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
games_dir="${KKBP_GAMES_DIR:-$repo/games}"

case "${1:-}" in
  kk)  target="$games_dir/Koikatsu/BepinEx/plugins/KKBP" ;;
  kks) target="$games_dir/Koikatsu Sunshine/BepinEx/plugins/KKBP" ;;
  svs) target="$games_dir/Summer Vacation Scramble/BepInEx/plugins/KKBP" ;;
  *) sed -n '2,6p' "$0" | sed 's/^# \{0,1\}//'; exit 1 ;;
esac

dll="$("$repo/scripts/build-exporters.sh" "$1")"
mkdir -p "$target"
cp "$dll" "$repo/LICENSE" "$repo/NOTICE" "$target/"
echo "Deployed $(basename "$dll") to $target"
