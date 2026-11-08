#!/usr/bin/env bash
# Runs one export in a game through the auto-export request (ADR 0012): writes
# BepInEx/config/kkbp-autoexport.json, starts the game with games/play.sh, waits for the plugin to
# write its result and quit, and prints the result. The plugin must be deployed first
# (scripts/deploy-exporter.sh). It refuses to start while the game is already running. Given a
# folder instead of a card, it runs the batch export on every card in it, one bundle each.
#
# Usage: scripts/auto-export.sh kk|kks|svs <card.png | card folder> <output folder> [extra request JSON members]
#   e.g. scripts/auto-export.sh kks card.png /tmp/out '"outfit": 0, "dump_shaders": "/tmp/s.json"'
# Paths in the extra members are written as given; use winpath-style or call this from export-sample.sh.
# Environment: KKBP_GAMES_DIR (default games/), KKBP_EXPORT_TIMEOUT seconds (default 900).
set -euo pipefail

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
games_dir="${KKBP_GAMES_DIR:-$repo/games}"
timeout="${KKBP_EXPORT_TIMEOUT:-900}"

[[ $# -ge 3 ]] || { sed -n '2,10p' "$0" | sed 's/^# \{0,1\}//'; exit 1; }
game="$1"; card="$(realpath "$2")"; out="$(realpath -m "$3")"; extra="${4:-}"
case "$game" in
  kk)  config="$games_dir/Koikatsu/BepinEx/config";                  play=koikatsu; exe=Koikatu.exe ;;
  kks) config="$games_dir/Koikatsu Sunshine/BepinEx/config";         play=kks;      exe=KoikatsuSunshine.exe ;;
  svs) config="$games_dir/Summer Vacation Scramble/BepInEx/config";  play=svs;      exe=SamabakeScramble.exe ;;
  *) echo "auto-export: unknown game '$game'" >&2; exit 1 ;;
esac
if [[ -d "$card" ]]; then
  what=folder
elif [[ -f "$card" ]]; then
  what=card
else
  echo "auto-export: no card or folder at $card" >&2; exit 1
fi

# The game's process, matched by its exact name (Linux keeps the first 15 characters). Matching the
# whole command line would also catch shells and editors that only mention the game.
proc="${exe:0:15}"
running() { pgrep -x "$proc" >/dev/null; }
# A game that is already open never reads the request, and stopping it at the timeout would close
# someone's session, so don't start.
if running; then
  echo "auto-export: $exe is already running; close it first" >&2
  exit 1
fi
# Each computer brings its own launcher ("The game launcher" in exporters/README.md).
if [[ ! -x "$games_dir/play.sh" ]]; then
  echo "auto-export: no executable game launcher at $games_dir/play.sh; copy scripts/play.example.sh there and adapt it" >&2
  exit 1
fi
mkdir -p "$out"

# Wine maps / to Z:, so the game sees Linux paths as Z:\…
winpath() { printf 'Z:%s' "${1//\//\\\\}"; }

request="$config/kkbp-autoexport.json"
result="$config/kkbp-autoexport.result.json"
rm -f "$result" "$config/kkbp-autoexport.continue"
printf '{ "%s": "%s", "output": "%s"%s }\n' "$what" "$(winpath "$card")" "$(winpath "$out")" "${extra:+, $extra}" > "$request"

"$games_dir/play.sh" "$play" >/dev/null 2>&1 &
deadline=$((SECONDS + timeout))
while [[ ! -f "$result" ]]; do
  if (( SECONDS > deadline )); then
    echo "auto-export: no result after ${timeout}s; stopping the game" >&2
    pkill -x "$proc" || true
    rm -f "$request"
    exit 1
  fi
  sleep 2
done
# Give the game a moment to quit on its own, then make sure it has.
for _ in $(seq 1 15); do running || break; sleep 2; done
pkill -x "$proc" 2>/dev/null || true
cat "$result"
grep -q '"state": "succeeded"' "$result"
