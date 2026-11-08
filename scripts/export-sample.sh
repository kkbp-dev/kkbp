#!/usr/bin/env bash
# Makes Golden Samples (ADR 0031): deploys each game's exporter, exports its Sample Card
# (contract/sample-cards/<game>.png) through the auto-export request (ADR 0012) with Outfit 00,
# physics on and nothing else, puts the bundle in contract/samples/<game>/ (ignored by git) with a
# stamp beside it, checks it against the contract, and then checks the imports against the
# committed importer snapshots.
#
# Usage: scripts/export-sample.sh [kk|kks|svs [card.png]]
#   With no Game it makes every Golden Sample whose game is installed, skips the others, and goes on
#   to the next Game when one fails; it fails at the end if any did.
# Environment: KKBP_GAMES_DIR (default games/).
set -euo pipefail

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$repo/scripts/golden-samples.sh"
games_dir="${KKBP_GAMES_DIR:-$repo/games}"
usage() { sed -n '2,11p' "$0" | sed 's/^# \{0,1\}//'; exit 1; }
work_root="$(mktemp -d)"
trap 'rm -rf "$work_root"' EXIT

# The install folder and process name (cut to Linux's 15 characters) of each Game.
install_of() {
  case "$1" in
    kk)  echo "$games_dir/Koikatsu" ;;
    kks) echo "$games_dir/Koikatsu Sunshine" ;;
    svs) echo "$games_dir/Summer Vacation Scramble" ;;
  esac
}
process_of() {
  case "$1" in kk) echo Koikatu.exe ;; kks) echo KoikatsuSunshin ;; svs) echo SamabakeScrambl ;; esac
}

# Called in an `if`, where `set -e` doesn't apply, so every step that can fail returns by hand.
export_one() {
  local game="$1" card="$2" work="$work_root/$1" bundle target
  [[ -f "$card" ]] || { echo "export-sample: no card at $card" >&2; return 1; }
  # A running game keeps the plugin it loaded and never reads the request; don't deploy into it.
  if pgrep -x "$(process_of "$game")" >/dev/null; then
    echo "export-sample: $game is running; close it first" >&2; return 1
  fi
  "$repo/scripts/deploy-exporter.sh" "$game" >&2 || return 1
  mkdir -p "$work" || return 1
  "$repo/scripts/auto-export.sh" "$game" "$card" "$work" \
    '"outfit": 0, "options": { "all_outfits": false, "all_variations": false, "physics": true, "enabled_shape_keys": false, "current_pose": false }' >&2 \
    || return 1
  bundle="$(find "$work" -mindepth 1 -maxdepth 1 -type d | head -1)"
  [[ -n "$bundle" && -f "$bundle/manifest.json" ]] || { echo "export-sample: the export wrote no Manifest" >&2; return 1; }
  target="$repo/contract/samples/$game"
  rm -rf "$target" "$target.stamp" && mkdir -p "$(dirname "$target")" && cp -r "$bundle" "$target" || return 1
  KKBP_EXPORTING_SAMPLE=1 "$repo/scripts/check-bundle.sh" "$target" || return 1
  golden_stamp > "$target.stamp" || return 1
  echo "Golden Sample written to $target" >&2
}

made=() failed=()
case "${1:-}" in
  "")
    for game in $(golden_games); do
      if [[ ! -d "$(install_of "$game")" ]]; then
        echo "notice: $game is not installed in $games_dir; its Golden Sample is skipped" >&2
      elif export_one "$game" "$repo/contract/sample-cards/$game.png"; then
        made+=("$game")
      else
        echo "export-sample: the $game Golden Sample was not made" >&2
        failed+=("$game")
      fi
    done ;;
  kk|kks|svs)
    if export_one "$1" "${2:-$repo/contract/sample-cards/$1.png}"; then made+=("$1"); else failed+=("$1"); fi ;;
  *) usage ;;
esac
(( ${#made[@]} )) || { echo "export-sample: no Golden Sample made" >&2; exit 1; }

# A Golden Sample from the Sample Cards should import as the committed snapshots record, with the
# physics bones within the physics tolerance.
echo "== Checking the imports against the snapshots" >&2
selected=()
for game in "${made[@]}"; do selected+=(--sample "$game"); done
python3 "$repo/importer/tests/harness/run.py" core "${selected[@]}"
python3 "$repo/importer/tests/harness/run.py" hooks "${selected[@]}"
(( ${#failed[@]} == 0 )) || { echo "export-sample: not made: ${failed[*]}" >&2; exit 1; }
